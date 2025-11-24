"""
项目配置文件
"""

import os
from typing import Dict, Any

# 基础配置
class Config:
    """基础配置类"""
    
    # 项目根目录
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 数据库配置
    DATABASE_URL = os.path.join(BASE_DIR, "data", "data.db")

    
    # 邮件服务配置
    MAIL_SERVER_PATH = os.path.join(BASE_DIR, "app", "mail_server.json")
    NOTICE_SERVER_PATH = os.path.join(BASE_DIR, "app", "notice_server.json")

    # 日志配置
    LOG_LEVEL = "INFO"
    
    # API配置
    API_RELOAD = False  # 默认关闭热重载
    API_DOCS = True    # 默认开启接口文档
    
    # 静态文件配置
    STATIC_DIR = os.path.join(BASE_DIR, "static")  # 静态文件目录


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    API_RELOAD = True  # 开发环境开启热重载
    API_DOCS = True   # 开发环境开启接口文档


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    API_RELOAD = False  # 生产环境关闭热重载
    API_DOCS = False   # 生产环境关闭接口文档


# 环境配置映射
configs: Dict[str, Any] = {
    "dev": DevelopmentConfig,
    "prod": ProductionConfig,
    "default": ProductionConfig
}


def get_config(env: str = None) -> Config:
    """获取配置实例"""
    if env is None:
        env = os.getenv("APP_ENV", "default")
    
    config_class = configs.get(env, configs["default"])
    return config_class()