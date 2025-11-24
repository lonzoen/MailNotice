"""
邮件通知系统主API
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth_api import router as auth_router
from app.api.email_configs_api import router as email_configs_router
# 邮箱相关API
from app.api.notification_channels_api import router as notification_channels_router
from app.middleware.auth_middleware import AuthMiddleware
# 通知相关API
from app.models.email_models import init_database
from app.services.schedule_service import start_schedule_service, stop_schedule_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# 获取根日志器并设置格式
root_logger = logging.getLogger()
formatter = logging.Formatter(
    fmt='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 为所有现有的处理器设置格式
for handler in root_logger.handlers:
    handler.setFormatter(formatter)

# 为所有子日志器设置格式（包括watchfiles等第三方库的日志器）
for name in logging.Logger.manager.loggerDict:
    logger_instance = logging.getLogger(name)
    # 移除所有现有的处理器
    for handler in logger_instance.handlers[:]:
        logger_instance.removeHandler(handler)
    # 添加根日志器的处理器
    for handler in root_logger.handlers:
        logger_instance.addHandler(handler)
    # 设置与根日志器相同的级别
    logger_instance.setLevel(root_logger.level)
    # 禁用向父级传播，避免重复日志
    logger_instance.propagate = False


def setup_logging_config():
    """设置统一的日志配置"""
    # 配置Uvicorn使用自定义的日志格式
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(levelname)s - %(asctime)s - %(name)s - %(message)s"
    log_config["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    log_config["formatters"]["access"]["fmt"] = "%(levelname)s - %(asctime)s - %(name)s  - \"%(request_line)s\" %(status_code)s"
    log_config["formatters"]["access"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    return log_config


# 导入配置
from config import get_config

# 创建lifespan事件处理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("邮件通知系统正在启动...")
    
    # 应用启动时初始化数据库
    init_database()
    
    # 启动定时任务服务（每5分钟检查一次邮件）
    start_schedule_service(interval_minutes=5)
    logger.info("邮件通知系统启动完成，定时任务服务已启动")
    
    yield
    
    # 应用关闭时的清理工作
    stop_schedule_service()
    logger.info("邮件通知系统关闭，定时任务服务已停止")

# 为不支持lifespan协议的ASGI服务器提供备选方案
async def on_startup():
    """应用启动事件处理器"""
    logger.info("通过事件处理器启动邮件通知系统...")
    
    # 应用启动时初始化数据库
    init_database()
    
    # 启动定时任务服务（每5分钟检查一次邮件）
    start_schedule_service(interval_minutes=5)
    logger.info("邮件通知系统启动完成，定时任务服务已启动")

async def on_shutdown():
    """应用关闭事件处理器"""
    # 应用关闭时的清理工作
    stop_schedule_service()
    logger.info("邮件通知系统关闭，定时任务服务已停止")


def create_app(config):
    """创建FastAPI应用实例"""
    # 创建FastAPI应用
    fastapi_kwargs = {
        "title": "邮件通知系统",
        "description": "基于FastAPI的邮件通知管理系统", 
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "lifespan": lifespan
    }

    # 如果API文档被禁用，显式禁用文档
    if not config.API_DOCS:
        fastapi_kwargs.update({
            "docs_url": None,
            "redoc_url": None
        })

    # 创建FastAPI应用
    app = FastAPI(**fastapi_kwargs)
    
    # 添加鉴权中间件
    app.add_middleware(AuthMiddleware)

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有服务器来源
        allow_credentials=True,
        allow_methods=["POST"],
        allow_headers=["*"],
    )

    # 注册路由
    # 认证相关API
    app.include_router(auth_router)
    
    # 邮箱相关API
    app.include_router(email_configs_router)

    # 通知相关API
    app.include_router(notification_channels_router)

    # 挂载静态文件服务
    app.mount("/", StaticFiles(directory=config.STATIC_DIR, html=True), name="static")
    
    return app

# 创建应用实例（使用默认配置）
default_config = get_config()
app = create_app(default_config)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"全局异常处理: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "message": str(exc)}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理"""
    logger.error(f"请求验证错误: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": "请求参数验证失败", "message": exc.errors().__str__()}
    )



if __name__ == "__main__":
    import argparse
    import uvicorn
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='邮件通知系统API服务器')
    parser.add_argument('--env', '-e', choices=['dev', 'prod'], default='prod',
                       help='运行环境: dev (开发环境) 或 prod (生产环境)')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 设置环境变量，让get_config函数能够获取到正确的环境
    os.environ['APP_ENV'] = args.env
    
    # 获取配置（基于命令行参数）
    config = get_config(args.env)
    
    logger.info(f"启动邮件通知系统API服务器 - 环境: {args.env}")
    
    # 根据配置显示文档地址
    if config.API_DOCS:
        logger.info("API文档地址: http://localhost:8080/docs")
        logger.info("ReDoc文档地址: http://localhost:8080/redoc")
    else:
        logger.info("API文档已禁用")

    # 使用统一的日志配置
    log_config = setup_logging_config()

    # 重新创建应用实例以使用新的配置
    app = create_app(config)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=config.API_RELOAD,  # 根据配置设置reload
        log_config=log_config
    )