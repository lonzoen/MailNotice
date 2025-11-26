"""
通知相关数据访问层
"""

from typing import List, Optional
from peewee import DoesNotExist
from app.models.email_models import NotificationChannel


class NotificationChannelRepository:
    """通知渠道数据访问类"""
    
    @staticmethod
    def get_all() -> List[NotificationChannel]:
        """获取所有通知渠道"""
        return list(NotificationChannel.select())
    
    @staticmethod
    def get_by_id(channel_id: int) -> Optional[NotificationChannel]:
        """根据ID获取通知渠道"""
        try:
            return NotificationChannel.get(NotificationChannel.id == channel_id)
        except DoesNotExist:
            return None
    
    @staticmethod
    def get_by_name(name: str) -> List[NotificationChannel]:
        """根据名称获取通知渠道"""
        return list(NotificationChannel.select().where(NotificationChannel.name == name))
    
    @staticmethod
    def create(name: str, token: str, server_name: str, chat_id: str = None) -> Optional[NotificationChannel]:
        """创建通知渠道"""
        return NotificationChannel.create(
            name=name,
            token=token,
            server_name=server_name,
            chat_id=chat_id
        )
    
    @staticmethod
    def update(channel_id: int, name: str = None, token: str = None, 
               server_name: str = None, chat_id: str = None) -> Optional[NotificationChannel]:
        """更新通知渠道"""
        try:
            channel = NotificationChannel.get(NotificationChannel.id == channel_id)
            if name is not None:
                channel.name = name
            if token is not None:
                channel.token = token
            if server_name is not None:
                channel.server_name = server_name
            if chat_id is not None:
                channel.chat_id = chat_id
            channel.save()
            return channel
        except DoesNotExist:
            return None
    
    @staticmethod
    def delete(channel_id: int) -> bool:
        """删除通知渠道"""
        try:
            channel = NotificationChannel.get(NotificationChannel.id == channel_id)
            channel.delete_instance()
            return True
        except DoesNotExist:
            return False