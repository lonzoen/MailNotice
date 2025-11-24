"""
鉴权中间件
提供简单的API请求拦截和鉴权功能
"""

import logging
import os
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import get_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """鉴权中间件"""
    
    # 类变量，用于缓存密码，避免重复读取文件
    _stored_password_cache = None
    _password_file_checked = False
    
    def __init__(self, app):
        super().__init__(app)
        self.config = get_config()
        # 从.password文件读取密码
        self.password_file = os.path.join(os.path.dirname(__file__), "..", "..", ".password")
        
        # 只在第一次实例化时读取密码文件
        if not AuthMiddleware._password_file_checked:
            AuthMiddleware._stored_password_cache = self._read_password_file()
            AuthMiddleware._password_file_checked = True
        
        self.stored_password = AuthMiddleware._stored_password_cache
        
        # 不需要鉴权的路径
        self.excluded_paths = {
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/api/login",  # 添加API登录路径
            "/favicon.ico"
        }
    
    def _read_password_file(self) -> str:
        """
        从.password文件读取密码，如果文件不存在则自动创建并生成随机密码
        
        Returns:
            str: 存储的密码
            如果密码文件不存在，会自动创建并生成随机密码
        """
        try:
            if os.path.exists(self.password_file):
                with open(self.password_file, 'r', encoding='utf-8') as f:
                    password = f.read().strip()
                    
                    if not password:
                        logger.warning("密码文件存在但内容为空，将重新生成密码")
                        return self._create_password_file()
                    
                    logger.info(f"成功从文件读取密码，密码长度: {len(password)}")
                    return password
            else:
                logger.info(f"密码文件不存在，将自动创建密码文件: {self.password_file}")
                return self._create_password_file()
        except Exception as e:
            logger.error(f"读取.password文件异常: {str(e)}")
            return ""
    
    def _create_password_file(self) -> str:
        """
        创建密码文件并生成随机密码
        
        Returns:
            str: 生成的随机密码
        """
        import secrets
        import string
        
        # 生成16位随机密码（包含字母、数字和特殊字符）
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(16))
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.password_file), exist_ok=True)
            
            # 写入密码文件
            with open(self.password_file, 'w', encoding='utf-8') as f:
                f.write(password)
            
            logger.info(f"生成的随机密码: {password}")

            return password
        except Exception as e:
            logger.error(f"创建密码文件失败: {str(e)}")
            return ""

    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理函数
            
        Returns:
            Response: 响应对象
        """
        # 检查是否在排除路径中
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        
        # 检查是否为API路径
        if request.url.path.startswith("/api/"):
            # 开发模式下禁用密码验证
            if self.config.DEBUG:
                logger.info("开发模式：密码验证已禁用")
                # 继续处理请求，不进行密码验证
                response = await call_next(request)
                return response
            
            try:
                # 获取密码（从Header中获取）
                password = self._extract_password(request)
                
                # 验证密码
                if not self._validate_password(password):
                    return JSONResponse(
                        status_code=401,
                        content={
                            "error": "Unauthorized",
                            "message": "无效的密码或缺少密码"
                        }
                    )
            except FileNotFoundError as e:
                logger.error(f"密码验证失败: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={"detail": "系统配置错误: 密码文件不存在"}
                )
            except Exception as e:
                logger.error(f"密码验证异常: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={"detail": "系统配置错误: 无法读取密码文件"}
                )
        
        # 继续处理请求
        response = await call_next(request)
        return response
    
    def _extract_password(self, request: Request) -> str:
        """
        从请求中提取密码
        
        Args:
            request: 请求对象
            
        Returns:
            str: 密码
        """
        # 从Header中获取（使用X-Password头）
        password = request.headers.get("X-Password")
        if password:
            return password
        
        return ""
    
    def _validate_password(self, password: Optional[str]) -> bool:
        """
        验证密码
        
        Args:
            password: 密码字符串
            
        Returns:
            bool: 验证是否通过
        """
        # 如果存储的密码为空，任何密码都不会验证通过
        if not self.stored_password:
            logger.warning("存储的密码为空，无法进行验证")
            return False
            
        if not password:
            logger.warning("输入密码为空")
            return False
        
        # 检查密码是否与存储的密码一致
        if password == self.stored_password:
            logger.info("密码验证通过")
            return True
        else:
            logger.warning(f"密码验证失败，输入密码长度: {len(password)}")
            return False