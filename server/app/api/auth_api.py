"""
认证相关API接口
直接调用中间件的验证密码服务
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

# 导入中间件验证服务
from app.middleware.auth_middleware import AuthMiddleware

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["认证管理"])


# Pydantic模型定义
class LoginRequest(BaseModel):
    """登录请求模型"""
    password: str


class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool
    message: str


# 创建中间件实例用于密码验证
_auth_middleware = AuthMiddleware(None)


def validate_password(password: Optional[str]) -> bool:
    """
    直接调用中间件的验证密码服务
    
    Args:
        password: 密码字符串
        
    Returns:
        bool: 验证是否通过
    """
    logger.info(f"调用中间件验证服务，接收到的密码为: {password}")
    
    # 直接调用中间件的验证方法
    return _auth_middleware._validate_password(password)


@router.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """
    用户登录接口 - 检查密码是否正确
    
    Args:
        login_request: 登录请求，包含密码
        
    Returns:
        LoginResponse: 登录结果
    """

    # 验证密码
    if validate_password(login_request.password):
        return LoginResponse(
            success=True,
            message="登录成功"
        )
    else:
        return LoginResponse(
            success=False,
            message="密码错误"
        )