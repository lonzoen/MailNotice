"""
邮件记录相关数据访问层
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from peewee import DoesNotExist, fn
from app.models.email_models import EmailContent


class EmailRecordRepository:
    """邮件记录数据访问类"""
    
    @staticmethod
    def get_all(limit: int = 100, offset: int = 0) -> List[EmailContent]:
        """获取所有邮件记录，支持分页"""
        return list(EmailContent.select()
                    .order_by(EmailContent.reception_time.desc())
                    .limit(limit)
                    .offset(offset))
    
    @staticmethod
    def get_by_id(email_id: int) -> Optional[EmailContent]:
        """根据ID获取邮件记录"""
        try:
            return EmailContent.get(EmailContent.id == email_id)
        except DoesNotExist:
            return None
    
    @staticmethod
    def get_by_recipient(recipient: str, limit: int = 100, offset: int = 0) -> List[EmailContent]:
        """根据收件人获取邮件记录"""
        return list(EmailContent.select()
                    .where(EmailContent.recipient == recipient)
                    .order_by(EmailContent.reception_time.desc())
                    .limit(limit)
                    .offset(offset))
    
    @staticmethod
    def get_by_sender(sender: str, limit: int = 100, offset: int = 0) -> List[EmailContent]:
        """根据发件人获取邮件记录"""
        return list(EmailContent.select()
                    .where(EmailContent.sender.contains(sender))
                    .order_by(EmailContent.reception_time.desc())
                    .limit(limit)
                    .offset(offset))
    
    @staticmethod
    def get_by_subject_keyword(keyword: str, limit: int = 100, offset: int = 0) -> List[EmailContent]:
        """根据主题关键词搜索邮件记录"""
        return list(EmailContent.select()
                    .where(EmailContent.subject.contains(keyword))
                    .order_by(EmailContent.reception_time.desc())
                    .limit(limit)
                    .offset(offset))
    
    @staticmethod
    def get_sent_emails(sent: bool = True, limit: int = 100, offset: int = 0) -> List[EmailContent]:
        """获取已发送/未发送的邮件记录"""
        return list(EmailContent.select()
                    .where(EmailContent.sent == sent)
                    .order_by(EmailContent.reception_time.desc())
                    .limit(limit)
                    .offset(offset))
    
    @staticmethod
    def get_recent_emails(hours: int = 24, limit: int = 100) -> List[EmailContent]:
        """获取最近指定小时内的邮件记录"""
        from datetime import timedelta
        since_time = datetime.now() - timedelta(hours=hours)
        return list(EmailContent.select()
                    .where(EmailContent.reception_time >= since_time)
                    .order_by(EmailContent.reception_time.desc())
                    .limit(limit))
    
    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """获取邮件统计信息"""
        total_emails = EmailContent.select().count()
        sent_emails = EmailContent.select().where(EmailContent.sent == True).count()
        unsent_emails = total_emails - sent_emails
        
        # 获取今日邮件数量
        today = datetime.now().date()
        today_emails = EmailContent.select().where(
            fn.date(EmailContent.reception_time) == today
        ).count()
        
        # 获取本周邮件数量
        week_start = today.replace(day=today.day - today.weekday())
        week_emails = EmailContent.select().where(
            fn.date(EmailContent.reception_time) >= week_start
        ).count()
        
        return {
            'total_emails': total_emails,
            'sent_emails': sent_emails,
            'unsent_emails': unsent_emails,
            'today_emails': today_emails,
            'week_emails': week_emails,
            'sent_rate': round((sent_emails / total_emails * 100), 2) if total_emails > 0 else 0
        }
    
    @staticmethod
    def mark_as_sent(email_id: int) -> bool:
        """标记邮件为已发送"""
        try:
            email = EmailContent.get(EmailContent.id == email_id)
            email.sent = True
            email.save()
            return True
        except DoesNotExist:
            return False
    
    @staticmethod
    def mark_as_unread(email_id: int) -> bool:
        """标记邮件为未发送"""
        try:
            email = EmailContent.get(EmailContent.id == email_id)
            email.sent = False
            email.save()
            return True
        except DoesNotExist:
            return False
    
    @staticmethod
    def delete(email_id: int) -> bool:
        """删除邮件记录"""
        try:
            email = EmailContent.get(EmailContent.id == email_id)
            email.delete_instance()
            return True
        except DoesNotExist:
            return False
    
    @staticmethod
    def create(sender: str, recipient: str, subject: str, reception_time: datetime = None, 
               body_text: str = None, sent: bool = False) -> Optional[EmailContent]:
        """创建新的邮件记录"""
        try:
            email = EmailContent.create(
                sender=sender,
                recipient=recipient,
                subject=subject,
                reception_time=reception_time or datetime.now(),
                body_text=body_text,
                sent=sent
            )
            return email
        except Exception:
            return None
    
    @staticmethod
    def batch_mark_sent(email_ids: List[int]) -> Dict[str, int]:
        """批量标记邮件为已发送"""
        success_count = 0
        failed_count = 0
        
        for email_id in email_ids:
            if EmailRecordRepository.mark_as_sent(email_id):
                success_count += 1
            else:
                failed_count += 1
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'total_count': len(email_ids)
        }
    
    @staticmethod
    def search_emails(keyword: str = None, sender: str = None, recipient: str = None, 
                     sent: bool = None, limit: int = 100, offset: int = 0) -> List[EmailContent]:
        """综合搜索邮件记录"""
        query = EmailContent.select()
        
        if keyword:
            query = query.where(
                (EmailContent.subject.contains(keyword)) |
                (EmailContent.body_text.contains(keyword))
            )
        
        if sender:
            query = query.where(EmailContent.sender.contains(sender))
        
        if recipient:
            query = query.where(EmailContent.recipient == recipient)
        
        if sent is not None:
            query = query.where(EmailContent.sent == sent)
        
        return list(query.order_by(EmailContent.reception_time.desc())
                   .limit(limit)
                   .offset(offset))