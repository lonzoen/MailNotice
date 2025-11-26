"""
邮件记录管理API接口 - 简化版本
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime

from app.repositories.email_record_repository import EmailRecordRepository

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


# 移除统计、搜索、批量操作相关模型 - 页面已简化


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


@router.get("/{email_id}", response_model=EmailRecordResponse)
async def get_email_by_id(email_id: int):
    """根据ID获取邮件记录"""
    try:
        email = EmailRecordRepository.get_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="邮件记录不存在")
        
        return {
            'id': email.id,
            'sender': email.sender,
            'recipient': email.recipient,
            'subject': email.subject,
            'reception_time': email.reception_time,
            'body_text': email.body_text,
            'sent': email.sent
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取邮件记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取邮件记录失败: {str(e)}")


@router.post("/", response_model=EmailRecordResponse)
async def create_email(email_data: EmailRecordCreate):
    """创建新的邮件记录"""
    try:
        email = EmailRecordRepository.create(
            sender=email_data.sender,
            recipient=email_data.recipient,
            subject=email_data.subject,
            reception_time=email_data.reception_time,
            body_text=email_data.body_text,
            sent=email_data.sent
        )
        
        if not email:
            raise HTTPException(status_code=400, detail="创建邮件记录失败")
        
        return {
            'id': email.id,
            'sender': email.sender,
            'recipient': email.recipient,
            'subject': email.subject,
            'reception_time': email.reception_time,
            'body_text': email.body_text,
            'sent': email.sent
        }
    except Exception as e:
        logger.error(f"创建邮件记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建邮件记录失败: {str(e)}")


@router.put("/{email_id}", response_model=EmailRecordResponse)
async def update_email(email_id: int, email_data: EmailRecordUpdate):
    """更新邮件记录"""
    try:
        email = EmailRecordRepository.get_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="邮件记录不存在")
        
        # 更新字段 - 注意：发送状态(sent)字段不能通过API手动修改
        if email_data.subject is not None:
            email.subject = email_data.subject
        if email_data.body_text is not None:
            email.body_text = email_data.body_text
        # 注意：不包含sent字段的更新，发送状态由系统自动管理
        
        email.save()
        
        return {
            'id': email.id,
            'sender': email.sender,
            'recipient': email.recipient,
            'subject': email.subject,
            'reception_time': email.reception_time,
            'body_text': email.body_text,
            'sent': email.sent
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新邮件记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新邮件记录失败: {str(e)}")


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

# 移除统计、搜索、过滤相关接口 - 页面已简化为仅邮件列表显示
# 移除搜索、过滤相关接口 - 页面已简化为仅邮件列表显示


# 移除手动发送和批量发送相关接口 - 发送功能由定时任务自动处理