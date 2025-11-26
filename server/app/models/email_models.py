"""
邮件通知系统数据模型
"""

import logging

from peewee import *

from config import get_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 获取全局配置
config = get_config()

# 创建数据库连接
db = SqliteDatabase(config.DATABASE_URL)

class BaseModel(Model):
    """基础模型类"""
    class Meta:
        database = db

class EmailConfig(BaseModel):
    """邮箱配置表"""
    account = CharField(max_length=100, primary_key=True)  # 邮箱账户
    auth_code = CharField(max_length=255)  # 授权码
    server_name = CharField(max_length=50)  # 服务商名称
    channel_id = CharField(max_length=50)

    class Meta:
        table_name = 'email_configs'



class NotificationChannel(BaseModel):
    """通知渠道表"""
    id = AutoField(primary_key=True)  # 渠道ID
    name = CharField(max_length=100)  # 渠道名称
    token = CharField(max_length=255)  # 认证令牌
    server_name = CharField(max_length=255)  # 服务器名称
    chat_id = CharField(max_length=50, null=True)  # Telegram聊天ID（仅Telegram渠道使用）
    
    class Meta:
        table_name = 'notification_channels'

class EmailContent(BaseModel):
    """邮件内容表"""
    id = AutoField(primary_key=True)  # 邮件ID
    sender = CharField(max_length=255)  # 发件人
    recipient = CharField(max_length=100)  # 邮箱账户
    subject = TextField()  # 邮件主题
    reception_time = DateTimeField()  # 接收时间
    body_text = TextField(null=True)  # 纯文本正文
    sent = BooleanField(default=False)  # 是否已发送通知

    class Meta:
        table_name = 'email_contents'

def create_tables():
    """创建数据库表"""
    db.connect()
    db.create_tables([
        EmailConfig,
        NotificationChannel,
        EmailContent
    ])
    logger.info("数据库表创建成功")

def init_database():
    """初始化数据库"""
    create_tables()

if __name__ == "__main__":
    init_database()