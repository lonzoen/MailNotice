"""
邮箱相关业务逻辑服务层
"""

import email
import json
import logging
import os
from datetime import datetime
from email.header import decode_header
from typing import List, Optional, Dict

from imapclient import IMAPClient

from app.models.email_models import EmailConfig, EmailContent
from app.repositories.email_repository import EmailConfigRepository

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailService:
    """邮箱业务服务类"""

    def __init__(self):
        # 加载邮件服务器配置
        self.server_configs = self._load_server_configs()

    def _load_server_configs(self) -> Dict[str, Dict[str, str]]:
        """加载邮件服务器配置"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                   'app', 'mail_server.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                servers = json.load(f)
                # 转换为字典格式，方便根据服务名查找
                return {server['name']: server for server in servers}
        except Exception as e:
            logger.error(f"加载邮件服务器配置失败: {e}")
            return {}

    def _get_server_config(self, server_name: str) -> Optional[Dict[str, str]]:
        """根据服务名获取服务器配置"""
        if server_name in self.server_configs:
            return self.server_configs[server_name]

        # 如果没有找到，使用默认的IMAP服务器地址
        default_config = {
            'name': server_name,
            'imap': f'imap.{server_name.lower()}.com'
        }
        logger.warning(f"未找到服务器配置 '{server_name}'，使用默认配置: {default_config}")
        return default_config

    def _decode_header_value(self, header_value: str) -> str:
        """解码邮件头信息"""
        if not header_value:
            return ''

        try:
            decoded_parts = decode_header(header_value)
            result = []
            for part, charset in decoded_parts:
                if isinstance(part, bytes):
                    # 如果有指定编码，则使用指定编码解码
                    if charset:
                        result.append(part.decode(charset, errors='replace'))
                    else:
                        # 否则尝试使用utf-8解码
                        result.append(part.decode('utf-8', errors='replace'))
                else:
                    result.append(part)
            return ''.join(result)
        except Exception as e:
            logger.error(f"解码邮件头失败: {e}")
            return header_value

    def _extract_email_content(self, email_message) -> str:
        """
        提取邮件正文
        
        Args:
            email_message: 邮件消息对象
            
        Returns:
            str: 邮件正文文本
        """
        body_text = ''

        try:
            # 遍历邮件的各个部分
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))

                    # 跳过附件
                    if 'attachment' in content_disposition:
                        continue

                    # 获取文本正文
                    if content_type == 'text/plain' and 'attachment' not in content_disposition:
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                # 尝试解码
                                charset = part.get_content_charset() or 'utf-8'
                                body_text += payload.decode(charset, errors='replace')
                        except Exception as e:
                            logger.warning(f"提取文本正文失败: {e}")

                    # 对于HTML邮件，提取纯文本内容
                    elif content_type == 'text/html' and 'attachment' not in content_disposition:
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                # 尝试解码
                                charset = part.get_content_charset() or 'utf-8'
                                html_content = payload.decode(charset, errors='replace')
                                # 简单提取HTML中的文本内容（去除标签）
                                import re
                                text_content = re.sub(r'<[^>]+>', ' ', html_content)
                                text_content = re.sub(r'\s+', ' ', text_content).strip()
                                body_text += text_content
                        except Exception as e:
                            logger.warning(f"提取HTML正文失败: {e}")

            else:
                # 单部分邮件
                content_type = email_message.get_content_type()
                
                if content_type == 'text/plain':
                    try:
                        payload = email_message.get_payload(decode=True)
                        if payload:
                            charset = email_message.get_content_charset() or 'utf-8'
                            body_text = payload.decode(charset, errors='replace')
                    except Exception as e:
                        logger.warning(f"提取单部分文本正文失败: {e}")
                
                elif content_type == 'text/html':
                    try:
                        payload = email_message.get_payload(decode=True)
                        if payload:
                            charset = email_message.get_content_charset() or 'utf-8'
                            html_content = payload.decode(charset, errors='replace')
                            # 简单提取HTML中的文本内容（去除标签）
                            import re
                            text_content = re.sub(r'<[^>]+>', ' ', html_content)
                            text_content = re.sub(r'\s+', ' ', text_content).strip()
                            body_text = text_content
                    except Exception as e:
                        logger.warning(f"提取单部分HTML正文失败: {e}")

        except Exception as e:
            logger.error(f"提取邮件内容失败: {e}")

        return body_text

    def fetch_emails(self, email_config: EmailConfig, get_body: bool = False, count: int = 5) -> List[EmailContent]:
        """
        使用IMAP协议收取邮件
        
        Args:
            email_config: 邮箱配置对象
            get_body: 是否获取邮件正文，默认为False
            
        Returns:
            List[EmailContent]: 邮件内容列表
        """
        email_contents = []

        try:
            # 获取服务器配置
            server_config = self._get_server_config(email_config.server_name)
            if not server_config:
                logger.error(f"未找到服务器配置: {email_config.server_name}")
                return email_contents

            imap_server = server_config.get('imap', '')
            if not imap_server:
                logger.error(f"IMAP服务器地址为空: {email_config.server_name}")
                return email_contents

            logger.info(f"连接IMAP服务器: {imap_server}，邮箱: {email_config.account}，获取正文: {get_body}")

            # 连接IMAP服务器 - 添加SSL连接选项
            with IMAPClient(imap_server, port=993, ssl=True, ssl_context=None) as client:
                # 登录邮箱
                client.login(email_config.account, email_config.auth_code)

                if server_config.get('name') == "126":
                    client.id_({"name": "MailNotice", "version": "1.0.0"})
                logger.info(f"邮箱登录成功: {email_config.account}")

                # 选择收件箱
                client.select_folder('INBOX')
                logger.info(f"选择收件箱成功: {email_config.account}")

                # 搜索所有邮件
                messages = client.search(['ALL'])
                logger.info(f"找到邮件数量: {len(messages)}，邮箱: {email_config.account}")

                # 只获取最近的5封邮件（避免一次性获取过多邮件）
                recent_messages = messages[-count:] if len(messages) > count else messages

                for msg_id in recent_messages:
                    try:
                        # 获取邮件头信息
                        header_data = client.fetch([msg_id], ['ENVELOPE'])
                        envelope = header_data[msg_id][b'ENVELOPE']

                        # 解析发件人
                        sender = ''
                        if envelope.from_:
                            sender = envelope.from_[0].mailbox.decode() + '@' + envelope.from_[0].host.decode()

                        # 解析主题
                        subject = self._decode_header_value(envelope.subject.decode() if envelope.subject else '')

                        # 解析接收时间
                        reception_time = datetime.now()
                        if envelope.date:
                            reception_time = envelope.date

                        # 初始化正文
                        body_text = ''

                        # 如果要求获取正文
                        if get_body:
                            try:
                                # 获取完整的邮件内容
                                full_data = client.fetch([msg_id], ['BODY.PEEK[]'])
                                raw_email = full_data[msg_id][b'BODY[]']
                                
                                # 解析邮件内容
                                email_message = email.message_from_bytes(raw_email)
                                
                                # 提取正文
                                body_text = self._extract_email_content(email_message)
                                
                            except Exception as e:
                                logger.warning(f"获取邮件正文失败 (ID: {msg_id}): {e}")

                        # 创建EmailContent对象
                        email_content = EmailContent(
                            sender=sender,
                            recipient=email_config.account,
                            subject=subject,
                            reception_time=reception_time,
                            body_text=body_text
                        )

                        email_contents.append(email_content)

                    except Exception as e:
                        logger.error(f"处理邮件失败 (ID: {msg_id}): {e}")
                        continue

                logger.info(f"成功获取邮件信息: {len(email_contents)}封，邮箱: {email_config.account}")

        except Exception as e:
            logger.error(f"收取邮件失败: {email_config.account}，错误: {e}")

        return email_contents


if __name__ == "__main__":
    """主函数，用于测试从数据库获取邮件配置并收取邮件"""

    # 创建EmailService实例
    email_service = EmailService()

    try:
        # 从数据库获取所有邮件配置
        logger.info("从数据库获取邮件配置...")
        all_configs = EmailConfigRepository.get_all()
        # all_configs = EmailConfigRepository.query(server_name="126")

        if not all_configs:
            logger.warning("数据库中没有找到邮件配置")
        else:
            logger.info(f"成功获取 {len(all_configs)} 个邮件配置")

            # 对每个配置进行测试
            for config in all_configs:
                logger.info(f"--- 测试邮箱配置: {config.account} ({config.server_name}) ---")


                # 收取邮件
                emails = email_service.fetch_emails(config)

                if emails:
                    logger.info(f"成功获取 {len(emails)} 封邮件信息")

                    # 打印前5封邮件的简要信息
                    logger.info("前5封邮件信息:")
                    for i, email in enumerate(emails[:5]):
                        logger.info(f"{i + 1}. 发件人: {email.sender}")
                        logger.info(f"   主题: {email.subject}")
                        logger.info(f"   接收时间: {email.reception_time}")
                        logger.info("   ---------------------------------")
                else:
                    logger.warning(f"未获取到邮件信息")

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()