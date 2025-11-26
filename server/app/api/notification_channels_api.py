"""
通知渠道相关API接口
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.repositories.notification_repository import NotificationChannelRepository

router = APIRouter(prefix="/api/notification-channels", tags=["通知渠道管理"])


# Pydantic模型定义
# 用于封装查询参数的模型
class ChannelIdQuery(BaseModel):
    channel_id: int


class NotificationChannelCreate(BaseModel):
    name: str
    token: str
    server_name: str
    chat_id: Optional[str] = None  # Telegram聊天ID


class NotificationChannelUpdate(BaseModel):
    name: Optional[str] = None
    token: Optional[str] = None
    server_name: Optional[str] = None
    channel_id: Optional[int] = None
    chat_id: Optional[str] = None  # Telegram聊天ID


# 用于封装update_channel接口参数的模型
class UpdateChannelRequest(ChannelIdQuery, NotificationChannelUpdate):
    pass


# 通知渠道API
@router.post("/get", response_model=List[dict])
async def get_all_channels():
    """获取所有通知渠道"""
    channels = NotificationChannelRepository.get_all()
    return [channel.__data__ for channel in channels]


@router.post("/add", response_model=dict)
async def create_channel(channel_data: NotificationChannelCreate):
    """创建通知渠道"""
    channel = NotificationChannelRepository.create(
        channel_data.name,
        channel_data.token,
        channel_data.server_name,
        channel_data.chat_id
    )
    if not channel:
        raise HTTPException(status_code=400, detail="创建失败")
    return channel.__data__


@router.post("/update", response_model=dict)
async def update_channel(request: UpdateChannelRequest):
    """更新通知渠道"""
    channel = NotificationChannelRepository.update(
        request.channel_id,
        request.name,
        request.token,
        request.server_name,
        request.chat_id
    )
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")
    return channel.__data__


@router.post("/delete")
async def delete_channel(query: ChannelIdQuery):
    """删除通知渠道"""
    success = NotificationChannelRepository.delete(query.channel_id)
    if not success:
        raise HTTPException(status_code=404, detail="渠道不存在")
    return {"message": "删除成功"}


@router.post("/test")
async def test_channel(channel: NotificationChannelCreate):
    """测试通知渠道"""
    try:
        # 导入NotificationService
        from app.services.notification_service import NotificationService

        # 调用NotificationService的send方法进行测试
        result = await NotificationService.send(
            name=channel.server_name,
            key=channel.token,
            content=channel.name,
            msg="这是一条测试消息",
            chat_id=channel.chat_id
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"测试失败: {str(e)}")


@router.post("/get_servers", response_model=List[str])
async def get_servers():
    """获取所有邮箱服务器名称"""
    import json
    import os

    # 读取mail_server.json文件
    json_file = os.path.join(os.path.dirname(__file__), "..", "notice_server.json")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 提取所有name属性
    servers = [item["name"] for item in data]
    return servers


