"""
邮箱相关数据访问层
"""

from typing import List, Optional
from datetime import datetime
from peewee import DoesNotExist
from app.models.email_models import EmailConfig, EmailContent


class EmailServiceProviderRepository:
    """邮箱服务商数据访问类"""


class EmailConfigRepository:
    """邮箱配置数据访问类"""

    @staticmethod
    def get_all() -> List[EmailConfig]:
        """获取所有邮箱配置"""
        return list(EmailConfig.select())

    @staticmethod
    def get_by_account(account: str) -> Optional[EmailConfig]:
        """根据账户获取邮箱配置"""
        try:
            return EmailConfig.get(EmailConfig.account == account)
        except DoesNotExist:
            return None

    @staticmethod
    def create(account: str, auth_code: str, server: str, server_name: str, channel_id: int) -> Optional[EmailConfig]:
        """创建邮箱配置"""
        return EmailConfig.create(
            account=account,
            auth_code=auth_code,
            server=server,
            server_name=server_name,
            channel_id=channel_id
        )

    @staticmethod
    def update(account: str, auth_code: str = None, server_name: str = None, channel_id: int = None) -> Optional[
        EmailConfig]:
        """更新邮箱配置"""
        try:
            config = EmailConfig.get(EmailConfig.account == account)
            if auth_code is not None:
                config.auth_code = auth_code
            if server_name is not None:
                config.server_name = server_name
            if channel_id is not None:
                config.channel_id = channel_id

            config.save()
            return config
        except DoesNotExist:
            return None

    @staticmethod
    def delete(account: str) -> bool:
        """删除邮箱配置"""
        try:
            config = EmailConfig.get(EmailConfig.account == account)
            config.delete_instance()
            return True
        except DoesNotExist:
            return False

    @staticmethod
    def query(
        account: str = None,
        server_name: str = None,
        channel_id: int = None,
        limit: int = None,
        offset: int = 0
    ) -> List[EmailConfig]:
        """
        动态查询邮箱配置
        
        Args:
            account: 邮箱账户，为空时不作为查询条件
            server_name: 服务器名称，为空时不作为查询条件
            channel_id: 频道ID，为空时不作为查询条件
            limit: 限制返回数量，为空时返回所有
            offset: 偏移量，用于分页
            
        Returns:
            List[EmailConfig]: 符合条件的邮箱配置列表
        """
        query = EmailConfig.select()
        
        # 动态构建查询条件
        if account is not None:
            query = query.where(EmailConfig.account == account)
        
        if server_name is not None:
            query = query.where(EmailConfig.server_name == server_name)
        
        if channel_id is not None:
            query = query.where(EmailConfig.channel_id == channel_id)
        
        # 应用分页
        if offset > 0:
            query = query.offset(offset)
        
        if limit is not None:
            query = query.limit(limit)
        
        return list(query)

    @staticmethod
    def count_dynamic(
        account: str = None,
        server_name: str = None,
        channel_id: int = None
    ) -> int:
        """
        动态统计符合条件的邮箱配置数量
        
        Args:
            account: 邮箱账户，为空时不作为查询条件
            server_name: 服务器名称，为空时不作为查询条件
            channel_id: 频道ID，为空时不作为查询条件
            
        Returns:
            int: 符合条件的邮箱配置数量
        """
        query = EmailConfig.select()
        
        # 动态构建查询条件
        if account is not None:
            query = query.where(EmailConfig.account == account)
        
        if server_name is not None:
            query = query.where(EmailConfig.server_name == server_name)
        
        if channel_id is not None:
            query = query.where(EmailConfig.channel_id == channel_id)
        
        return query.count()


class EmailContentRepository:
    """邮件内容数据访问类"""

    @staticmethod
    def get_all() -> List[EmailContent]:
        """获取所有邮件内容"""
        return list(EmailContent.select())

    @staticmethod
    def get_by_id(email_id: int) -> Optional[EmailContent]:
        """根据ID获取邮件内容"""
        try:
            return EmailContent.get(EmailContent.id == email_id)
        except DoesNotExist:
            return None

    @staticmethod
    def get_by_account(account: str) -> List[EmailContent]:
        """根据邮箱账户获取邮件内容"""
        return list(EmailContent.select().where(EmailContent.recipient == account))

    @staticmethod
    def create(sender: str, subject: str, reception_time: datetime, body_text: str,
               config_account: str, body_html: str = '', attachments_count: int = 0) -> Optional[EmailContent]:
        """创建邮件内容"""
        return EmailContent.create(
            sender=sender,
            subject=subject,
            reception_time=reception_time,
            body_text=body_text,
            body_html=body_html,
            attachments_count=attachments_count,
            config_account=config_account
        )

    @staticmethod
    def update(email_id: int, is_read: bool = None) -> Optional[EmailContent]:
        """更新邮件内容"""
        try:
            email = EmailContent.get(EmailContent.id == email_id)
            if is_read is not None:
                email.is_read = is_read
            email.save()
            return email
        except DoesNotExist:
            return None

    @staticmethod
    def delete(email_id: int) -> bool:
        """删除邮件内容"""
        try:
            email = EmailContent.get(EmailContent.id == email_id)
            email.delete_instance()
            return True
        except DoesNotExist:
            return False