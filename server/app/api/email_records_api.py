"""
邮件记录管理API接口 - 简化版本
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime

from app.repositories.email_record_repository import EmailRecordRepository
from app.services.notification_service import NotificationService
from app.repositories.notification_repository import NotificationChannelRepository
from app.repositories.email_repository import EmailConfigRepository

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email-records", tags=["邮件记录管理"])


# Pydantic模型定义
class EmailRecordBase(BaseModel):
    """邮件记录基础模型"""
    sender: str
    recipient: str
    subject: str
    body_text: Optional[str] = None
    sent: bool = False


class EmailRecordCreate(EmailRecordBase):
    """创建邮件记录"""
    reception_time: Optional[datetime] = None


class EmailRecordUpdate(BaseModel):
    """更新邮件记录"""
    subject: Optional[str] = None
    body_text: Optional[str] = None
    # 移除sent字段 - 发送状态应由系统自动设置，不能手动修改


class EmailRecordResponse(EmailRecordBase):
    """邮件记录响应模型"""
    id: int
    reception_time: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[EmailRecordResponse])
async def get_all_emails(
    limit: int = Query(100, ge=1, le=1000, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """获取所有邮件记录"""
    try:
        emails = EmailRecordRepository.get_all(limit=limit, offset=offset)
        return [
            {
                'id': email.id,
                'sender': email.sender,
                'recipient': email.recipient,
                'subject': email.subject,
                'reception_time': email.reception_time,
                'body_text': email.body_text,
                'sent': email.sent
            }
            for email in emails
        ]
    except Exception as e:
        logger.error(f"获取邮件记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取邮件记录失败: {str(e)}")


@router.delete("/{email_id}")
async def delete_email(email_id: int):
    """删除邮件记录 - 仅用于管理员手动清理不必要的邮件记录"""
    try:
        success = EmailRecordRepository.delete(email_id)
        if not success:
            raise HTTPException(status_code=404, detail="邮件记录不存在")
        
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除邮件记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除邮件记录失败: {str(e)}")

# 手动发送邮件通知请求模型
class SendManualRequest(BaseModel):
    """手动发送邮件通知请求"""
    email_id: int

# 手动发送邮件通知接口
@router.post("/send-manual", response_model=dict)
async def send_email_manual(request: SendManualRequest):
    """手动发送邮件通知"""
    email_id = request.email_id
    try:
        # 获取邮件记录
        email = EmailRecordRepository.get_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="邮件记录不存在")
        
        # 检查邮件是否已经发送过
        if email.sent:
            raise HTTPException(status_code=400, detail="该邮件已经发送过通知")
        
        # 获取邮箱配置
        email_config = EmailConfigRepository.get_by_account(email.recipient)
        if not email_config:
            raise HTTPException(status_code=404, detail=f"未找到邮箱配置: {email.recipient}")
        
        # 获取通知渠道配置
        channel = NotificationChannelRepository.get_by_id(int(email_config.channel_id))
        if not channel:
            raise HTTPException(status_code=404, detail=f"未找到通知渠道: {email_config.channel_id}")
        
        # 构建通知内容
        content = email.subject if email.subject else "无主题"
        message = f"发件人：{email.sender}\n" \
                 f"收件人：{email.recipient}\n" \
                 f"收件时间：{email.reception_time}\n" \
                 f"主题：{content}\n" \
                 f"正文：\n{email.body_text if email.body_text else '无正文内容'}\n"
        
        # 发送通知
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
            
            logger.info(f"手动发送邮件通知成功: {email.sender} -> {email.recipient}, 主题: {content[:20]}...")
            return {
                "success": True,
                "message": "邮件通知发送成功",
                "data": result
            }
        else:
            # 发送失败
            error_msg = result.get('message', '未知错误') if result else '通知服务返回失败'
            logger.error(f"手动发送邮件通知失败: {email.sender} -> {email.recipient}, 错误: {error_msg}")
            raise HTTPException(status_code=500, detail=f"发送通知失败: {error_msg}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动发送邮件通知异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发送通知异常: {str(e)}")