"""
定时任务服务
使用APScheduler实现邮箱邮件收取和通知推送的定时任务
"""

import asyncio
import logging
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
        处理单个邮箱配置：收取邮件、对比新邮件、推送通知
        
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
            # 1. 收取邮件（不获取正文，提高效率）
            logger.info(f"开始收取邮件: {email_config.account}")
            emails = self.email_service.fetch_emails(email_config, get_body=False)
            result['total_emails'] = len(emails)
            
            if not emails:
                logger.info(f"未收到邮件: {email_config.account}")
                return result
            
            # 2. 检查数据库是否为空
            existing_emails = EmailContent.select().where(
                EmailContent.recipient == email_config.account
            )
            
            if not existing_emails:
                # 数据库为空，将收取到的邮件存入数据库
                logger.info(f"数据库为空，将收取到的 {len(emails)} 封邮件存入数据库: {email_config.account}")
                for email in emails:
                    email.save()
                result['new_emails'] = len(emails)
            else:
                # 数据库不为空，对比新邮件
                logger.info(f"数据库已有邮件，开始对比新邮件: {email_config.account}")
                
                # 对比逻辑：基于发件人、主题、接收时间的组合来判断是否为新邮件
                new_emails = []
                for email in emails:
                    # 检查是否已存在相同特征的邮件
                    existing = EmailContent.select().where(
                        (EmailContent.recipient == email_config.account) &
                        (EmailContent.sender == email.sender) &
                        (EmailContent.reception_time == email.reception_time)
                    ).first()
                    
                    if not existing:
                        new_emails.append(email)
                
                # 保存新邮件到数据库，并删除相同数量的旧邮件
                if new_emails:
                    # 重新获取新邮件的正文内容
                    logger.info(f"检测到 {len(new_emails)} 封新邮件，开始获取正文内容")
                    
                    # 重新获取新邮件的完整内容（包括正文）
                    new_emails_with_body = self.email_service.fetch_emails(email_config, get_body=True)
                    
                    # 创建新邮件映射，用于匹配正文
                    new_emails_map = {}
                    for email in new_emails_with_body:
                        key = (email.sender, email.reception_time)
                        new_emails_map[key] = email
                    
                    # 更新新邮件的正文内容
                    updated_new_emails = []
                    for email in new_emails:
                        key = (email.sender, email.reception_time)
                        if key in new_emails_map:
                            email_with_body = new_emails_map[key]
                            email.body_text = email_with_body.body_text
                        updated_new_emails.append(email)
                    
                    new_email_count = len(new_emails)
                    
                    # 先发送通知
                    if new_email_count > 0:
                        await self.send_notifications(email_config, updated_new_emails)
                        result['notifications_sent'] = new_email_count
                    
                    # 再保存新邮件（包含正文）
                    for email in updated_new_emails:
                        email.save()
                    
                    # 检查当前邮箱的邮件总数
                    total_emails = EmailContent.select().where(
                        EmailContent.recipient == email_config.account
                    ).count()
                    
                    # 如果邮件总数超过5封，删除超过5封的旧邮件
                    deleted_count = 0
                    if total_emails > 5:
                        # 计算需要删除的邮件数量
                        emails_to_delete = total_emails - 5
                        
                        # 获取最旧的邮件（按收件时间从旧到新）
                        oldest_emails = EmailContent.select().where(
                            EmailContent.recipient == email_config.account
                        ).order_by(EmailContent.reception_time.asc()).limit(emails_to_delete)
                        
                        # 删除旧邮件
                        for old_email in oldest_emails:
                            old_email.delete_instance()
                            deleted_count += 1
                        
                        logger.info(f"邮箱 {email_config.account} 邮件总数 {total_emails} 超过5封，删除 {deleted_count} 封旧邮件")
                    
                    result['new_emails'] = new_email_count
                    result['deleted_old_emails'] = deleted_count
                    logger.info(f"发现 {new_email_count} 封新邮件，删除 {deleted_count} 封旧邮件: {email_config.account}")
                else:
                    logger.info(f"没有发现新邮件: {email_config.account}")
            
            logger.info(f"处理完成: {email_config.account}, 新邮件: {result['new_emails']}")
            
        except Exception as e:
            error_msg = f"处理邮箱配置失败: {email_config.account}, 错误: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    async def send_notifications(self, email_config: EmailConfig, new_emails: List[EmailContent]) -> None:
        """
        发送新邮件通知
        
        Args:
            email_config: 邮箱配置对象
            new_emails: 新邮件列表
        """
        try:
            # 获取通知渠道配置
            channel = NotificationChannelRepository.get_by_id(int(email_config.channel_id))
            
            if not channel:
                logger.warning(f"未找到通知渠道: {email_config.channel_id}")
                return
            
            if not new_emails:
                logger.warning(f"没有新邮件需要通知: {email_config.account}")
                return
            
            # 获取最新的新邮件（按收件时间从新到旧）
            latest_new_email = max(new_emails, key=lambda x: x.reception_time)
            
            # 构建通知内容
            content = latest_new_email.subject if latest_new_email.subject else "无主题"
            message = f"发件人：{latest_new_email.sender}\n" \
                     f"收件人：{latest_new_email.recipient}\n" \
                     f"收件时间：{latest_new_email.reception_time}\n" \
                     f"正文：\n{latest_new_email.body_text if latest_new_email.body_text else '无正文内容'}\n" \

            # 发送通知
            await NotificationService.send(
                name=channel.server_name,
                key=channel.token,
                content=content,
                msg=message
            )
            
            logger.info(f"通知发送成功: {email_config.account} -> {channel.name}, 新邮件数: {len(new_emails)}")
            
        except Exception as e:
            logger.error(f"发送通知失败: {email_config.account}, 错误: {str(e)}")
    
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