"""
邮箱配置相关API接口
"""

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.repositories.email_repository import EmailConfigRepository
from app.repositories.notification_repository import NotificationChannelRepository
from app.services.email_service import EmailService
from app.models.email_models import EmailConfig
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email-configs", tags=["邮箱配置管理"])


# Pydantic模型定义
# 用于封装查询参数的模型
class AccountQuery(BaseModel):
    account: str


class EmailSuffixQuery(BaseModel):
    email_suffix: str


class EmailConfigCreate(BaseModel):
    account: str
    auth_code: str
    server: str
    server_name: str
    channel_id: int


class EmailConfigTest(BaseModel):
    account: str
    auth_code: str
    server_name: str
    channel_id: int = 1


# 邮箱配置API
@router.post("/get", response_model=List[dict])
async def get_configs():
    """获取所有邮箱配置"""
    configs = EmailConfigRepository.get_all()
    return [config.__data__ for config in configs]

@router.post("/get_servers", response_model=List[str])
async def get_servers():
    """获取所有邮箱服务器名称"""
    import json
    import os
    
    # 读取mail_server.json文件
    json_file = os.path.join(os.path.dirname(__file__), "..", "mail_server.json")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取所有name属性
    servers = [item["name"] for item in data]
    return servers


@router.post("/add", response_model=dict)
async def add_config(config_data: EmailConfigCreate):
    """创建邮箱配置"""
    config = EmailConfigRepository.create(
        config_data.account,
        config_data.auth_code,
        config_data.server,
        config_data.server_name,
        config_data.channel_id
    )
    if not config:
        return {
            "success": False,
            "message": "创建失败"
        }
    return {
        "success": True,
        "message": "创建成功",
        "data": config.__data__
    }

@router.post("/update", response_model=dict)
async def update_config(config_data: EmailConfigCreate):
    """更新邮箱配置"""
    config = EmailConfigRepository.update(
        config_data.account,
        config_data.auth_code,
        config_data.server_name,
        config_data.channel_id
    )
    if not config:
        return {
            "success": False,
            "message": "配置不存在"
        }
    return {
        "success": True,
        "message": "更新成功",
        "data": config.__data__
    }

@router.post("/delete")
async def remove_config(query: AccountQuery):
    """删除邮箱配置"""
    success = EmailConfigRepository.delete(query.account)
    if not success:
        return {
            "success": False,
            "message": "配置不存在"
        }
    return {
        "success": True,
        "message": "删除成功"
    }

@router.post("/test", response_model=dict)
async def test_mail_config(config: EmailConfigTest):
    """测试单个邮箱配置（直接传入配置对象）"""
    email_service = EmailService()
    logger.info(f"--- 测试邮箱配置: {config.account} ({config.server_name}) ---")
    
    # 创建EmailConfig对象用于测试
    from app.models.email_models import EmailConfig
    test_config_obj = EmailConfig(
        account=config.account,
        auth_code=config.auth_code,
        server_name=config.server_name,
        channel_id=str(config.channel_id)
    )
    
    try:
        emails = email_service.fetch_emails(test_config_obj)
        
        return {
            "success": True,
            "message": f"成功获取{len(emails)}封邮件"
        }
    except Exception as e:
        logger.error(f"测试邮箱配置失败: {str(e)}")
        return {
            "success": False,
            "message": f"测试失败: {str(e)}"
        }

@router.post("/run_schedule", response_model=dict)
async def run_schedule():
    """立即运行一次定时任务"""
    logger.info("=== 开始执行手动邮件收取任务 ===")
    
    try:
        # 导入定时任务服务
        from app.services.schedule_service import run_once
        
        # 执行一次定时任务
        results = await run_once()
        
        # 统计汇总
        total_new_emails = sum(r.get('new_emails', 0) for r in results)
        total_notifications = sum(r.get('notifications_sent', 0) for r in results)
        total_errors = sum(len(r.get('errors', [])) for r in results)
        
        logger.info("=== 手动任务执行完成 ===")
        logger.info(f"总新邮件数: {total_new_emails}")
        logger.info(f"总通知发送数: {total_notifications}")
        logger.info(f"总错误数: {total_errors}")
        
        return {
            "success": True,
            "message": f"定时任务执行完成，发现{total_new_emails}封新邮件，发送{total_notifications}条通知",
            "data": {
                "total_new_emails": total_new_emails,
                "total_notifications": total_notifications,
                "total_errors": total_errors,
                "results": results
            }
        }
    except Exception as e:
        logger.error(f"执行定时任务失败: {str(e)}")
        return {
            "success": False,
            "message": f"定时任务执行失败: {str(e)}"
        }