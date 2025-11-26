"""
定时任务服务
使用APScheduler实现邮箱邮件收取和通知推送的定时任务
"""

import asyncio
import logging
from time import sleep
from typing import List, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from app.models.email_models import EmailConfig, EmailContent
from app.repositories.email_repository import EmailConfigRepository
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.repositories.notification_repository import NotificationChannelRepository

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScheduleService:
    """定时任务服务类"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Shanghai'))
        self.is_running = False
    
    async def process_email_config(self, email_config: EmailConfig) -> Dict[str, Any]:
        """
        处理单个邮箱配置：收取邮件、保存到数据库、推送未发送通知的邮件
        
        Args:
            email_config: 邮箱配置对象
            
        Returns:
            处理结果字典
        """
        result = {
            'account': email_config.account,
            'server_name': email_config.server_name,
            'total_emails': 0,
            'new_emails': 0,
            'deleted_old_emails': 0,
            'notifications_sent': 0,
            'errors': []
        }
        
        try:
            # 1. 收取邮件（获取正文，直接保存到数据库）
            logger.info(f"开始收取邮件: {email_config.account}")
            emails = self.email_service.fetch_emails(email_config, get_body=True)
            result['total_emails'] = len(emails)
            
            if not emails:
                logger.info(f"未收到邮件: {email_config.account}")
                return result
            
            # 2. 保存所有邮件到数据库（sent字段默认为False）
            new_emails = []
            for email in emails:
                # 检查是否已存在相同特征的邮件
                existing = EmailContent.select().where(
                    (EmailContent.recipient == email_config.account) &
                    (EmailContent.sender == email.sender) &
                    (EmailContent.reception_time == email.reception_time)
                ).first()
                
                if not existing:
                    # 新邮件，保存到数据库（sent=False）
                    email.sent = False  # 确保sent字段为False
                    email.save()
                    new_emails.append(email)
                    logger.info(f"保存新邮件到数据库: {email.sender} -> {email.recipient}, 主题: {email.subject}")
            
            result['new_emails'] = len(new_emails)
            
            # 3. 查找并发送未发送通知的邮件
            unsent_emails = EmailContent.select().where(
                (EmailContent.recipient == email_config.account) &
                (EmailContent.sent == False)
            ).order_by(EmailContent.reception_time.desc())
            
            if unsent_emails:
                logger.info(f"发现 {len(unsent_emails)} 封未发送通知的邮件: {email_config.account}")
                
                # 发送通知
                sent_count = await self.send_notifications_and_update_status(email_config, list(unsent_emails))
                result['notifications_sent'] = sent_count
                
                logger.info(f"成功发送 {sent_count} 封邮件的通知: {email_config.account}")
            else:
                logger.info(f"没有未发送通知的邮件: {email_config.account}")
            
            # 4. 检查并删除旧邮件（只删除已发送通知的邮件）
            total_emails = EmailContent.select().where(
                EmailContent.recipient == email_config.account
            ).count()
            
            deleted_count = 0
            if total_emails > 5:
                # 计算需要删除的邮件数量
                emails_to_delete = total_emails - 5
                
                # 获取最旧的已发送通知的邮件（按收件时间从旧到新）
                oldest_sent_emails = EmailContent.select().where(
                    (EmailContent.recipient == email_config.account) &
                    (EmailContent.sent == True)
                ).order_by(EmailContent.reception_time.asc()).limit(emails_to_delete)
                
                # 删除旧邮件
                for old_email in oldest_sent_emails:
                    old_email.delete_instance()
                    deleted_count += 1
                
                if deleted_count > 0:
                    logger.info(f"邮箱 {email_config.account} 邮件总数 {total_emails} 超过5封，删除 {deleted_count} 封已发送通知的旧邮件")
            
            result['deleted_old_emails'] = deleted_count
            logger.info(f"处理完成: {email_config.account}, 新邮件: {result['new_emails']}, 发送通知: {result['notifications_sent']}, 删除旧邮件: {result['deleted_old_emails']}")
            
        except Exception as e:
            error_msg = f"处理邮箱配置失败: {email_config.account}, 错误: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    async def send_notifications_and_update_status(self, email_config: EmailConfig, unsent_emails: List[EmailContent]) -> int:
        """
        发送未发送通知的邮件，并在发送成功后更新sent字段
        
        Args:
            email_config: 邮箱配置对象
            unsent_emails: 未发送通知的邮件列表
            
        Returns:
            成功发送通知的邮件数量
        """
        sent_count = 0
        failed_emails = []
        
        try:
            # 获取通知渠道配置
            channel = NotificationChannelRepository.get_by_id(int(email_config.channel_id))
            
            if not channel:
                logger.warning(f"未找到通知渠道: {email_config.channel_id}")
                return sent_count
            
            if not unsent_emails:
                logger.warning(f"没有未发送通知的邮件: {email_config.account}")
                return sent_count
            
            # 按收件时间从新到旧排序，优先发送最新的邮件
            unsent_emails.sort(key=lambda x: x.reception_time, reverse=True)
            
            logger.info(f"开始处理 {len(unsent_emails)} 封未发送邮件: {email_config.account}")
            
            for email in unsent_emails:
                try:
                    # 构建通知内容
                    content = email.subject if email.subject else "无主题"
                    message = f"发件人：{email.sender}\n" \
                             f"收件人：{email.recipient}\n" \
                             f"收件时间：{email.reception_time}\n" \
                             f"主题：{content}\n" \
                             f"正文：\n{email.body_text if email.body_text else '无正文内容'}\n"
                    
                    # 发送通知 - 只有成功才更新状态
                    result = await NotificationService.send(
                        name=channel.server_name,
                        key=channel.token,
                        content=content,
                        msg=message,
                        chat_id=channel.chat_id
                    )
                    
                    # 检查发送结果
                    if result and result.get('success', False):
                        # 发送成功，更新sent字段为True
                        email.sent = True
                        email.save()
                        
                        sent_count += 1
                        logger.info(f"✅ 邮件通知发送成功并标记为已发送: {email.sender} -> {email.recipient}, 主题: {content[:20]}...")
                    else:
                        # 发送失败，记录失败信息
                        error_msg = result.get('message', '未知错误') if result else '通知服务返回失败'
                        failed_emails.append(f"{email.sender} -> {email.recipient} ({error_msg})")
                        logger.warning(f"❌ 邮件通知发送失败: {email.sender} -> {email.recipient}, 错误: {error_msg}")
                    
                    # 添加短暂延迟，避免发送过快
                    sleep(0.5)
                    
                except Exception as e:
                    error_msg = str(e)
                    failed_emails.append(f"{email.sender} -> {email.recipient} ({error_msg})")
                    logger.error(f"❌ 发送邮件通知异常: {email.sender} -> {email.recipient}, 错误: {error_msg}")
                    # 发送异常，保持sent=False，下次继续尝试发送
            
            # 记录处理结果
            if failed_emails:
                logger.warning(f"⚠️ {email_config.account} 有 {len(failed_emails)} 封邮件发送失败: {failed_emails}")
            
            logger.info(f"📊 邮件通知发送完成: 成功 {sent_count}/{len(unsent_emails)} 封邮件: {email_config.account}")
            
        except Exception as e:
            logger.error(f"❌ 发送邮件通知过程失败: {email_config.account}, 错误: {str(e)}")
        
        return sent_count
    
    async def run_scheduled_task(self) -> List[Dict[str, Any]]:
        """
        执行定时任务
        
        Returns:
            所有邮箱配置的处理结果列表
        """
        logger.info("=== 开始执行定时邮件收取任务 ===")
        
        # 获取所有邮箱配置
        email_configs = EmailConfigRepository.get_all()
        
        if not email_configs:
            logger.warning("未找到邮箱配置，跳过定时任务")
            return []
        
        logger.info(f"找到 {len(email_configs)} 个邮箱配置")
        
        # 并行处理所有邮箱配置
        tasks = [self.process_email_config(config) for config in email_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"处理邮箱配置失败: {email_configs[i].account}, 错误: {str(result)}")
                valid_results.append({
                    'account': email_configs[i].account,
                    'errors': [str(result)]
                })
            else:
                valid_results.append(result)
        
        # 统计汇总
        total_new_emails = sum(r.get('new_emails', 0) for r in valid_results)
        total_notifications = sum(r.get('notifications_sent', 0) for r in valid_results)
        
        logger.info(f"=== 定时任务完成 ===")
        logger.info(f"总新邮件数: {total_new_emails}")
        logger.info(f"总通知发送数: {total_notifications}")
        
        return valid_results
    
    def start_scheduler(self, interval_minutes: int = 5) -> None:
        """
        启动定时调度器
        
        Args:
            interval_minutes: 定时任务间隔（分钟）
        """
        if self.is_running:
            logger.warning("定时调度器已在运行中")
            return
        
        # 添加定时任务
        self.scheduler.add_job(
            func=lambda: asyncio.run(self.run_scheduled_task()),
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='email_check_job',
            name='邮件检查任务',
            replace_existing=True
        )
        
        # 启动调度器
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"APScheduler定时调度器已启动，每 {interval_minutes} 分钟执行一次，时区: Asia/Shanghai")
    
    def stop_scheduler(self) -> None:
        """停止定时调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("APScheduler定时调度器已停止")
        else:
            logger.warning("APScheduler定时调度器未运行")


# 全局定时服务实例
schedule_service = ScheduleService()


def start_schedule_service(interval_minutes: int = 5) -> None:
    """
    启动定时服务（供外部调用）
    
    Args:
        interval_minutes: 定时任务间隔（分钟）
    """
    schedule_service.start_scheduler(interval_minutes)


def stop_schedule_service() -> None:
    """停止定时服务（供外部调用）"""
    schedule_service.stop_scheduler()


async def run_once() -> List[Dict[str, Any]]:
    """
    手动执行一次定时任务（供测试或手动调用）
    
    Returns:
        处理结果列表
    """
    return await schedule_service.run_scheduled_task()


if __name__ == "__main__":
    """直接运行一次定时任务"""
    # 直接运行一次定时任务
    async def main():
        logger.info("=== 开始执行手动邮件收取任务 ===")
        results = await schedule_service.run_scheduled_task()
        
        logger.info("=== 手动任务执行结果 ===")
        for result in results:
            logger.info(f"邮箱: {result.get('account')}, 新邮件: {result.get('new_emails', 0)}, 删除旧邮件: {result.get('deleted_old_emails', 0)}")
        
        # 统计汇总
        total_new_emails = sum(r.get('new_emails', 0) for r in results)
        total_notifications = sum(r.get('notifications_sent', 0) for r in results)
        logger.info(f"总新邮件数: {total_new_emails}")
        logger.info(f"总通知发送数: {total_notifications}")

    asyncio.run(main())