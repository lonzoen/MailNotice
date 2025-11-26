from typing import Dict, Any, Coroutine
import httpx
import json
import os
from telegram import Bot


class NotificationService:
    """通知服务类"""

    @staticmethod
    async def send(name: str, key: str, content: str, msg: str, group_id: str = None, chat_id: str = None) -> Dict[str, Any]:
        """
        发送通知
        
        Args:
            name: 通知渠道名称
            key: 应用密钥
            content: 通知内容
            msg: 消息内容
            group_id: 群组ID（可选）
            chat_id: Telegram聊天ID（可选）
            
        Returns:
            发送成功的结果字典
            
        Raises:
            Exception: 当发送失败或配置不存在时抛出异常
        """
        # 从notice_server.json获取服务器配置
        server_config = await NotificationService._get_server_config(name)
        if not server_config:
            raise Exception(f"未找到名称为 '{name}' 的通知服务商配置")

        # 根据不同的name执行不同的发送逻辑
        if name == "传息":
            return await NotificationService._send_chuanxi(server_config, key, content, msg, group_id)
        elif name == "企业微信":
            return await NotificationService._send_wechat_work(server_config, key, content, msg)
        elif name == "Telegram":
            return await NotificationService._send_telegram(server_config, key, content, msg, chat_id)
        else:
            raise Exception(f"暂时不支持 '{name}' 的通知服务商配置")

    @staticmethod
    async def _get_server_config(name: str) -> Any | None:
        """从notice_server.json获取服务器配置"""
        try:
            # 获取notice_server.json文件路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            server_file = os.path.join(current_dir, "..", "notice_server.json")

            with open(server_file, 'r', encoding='utf-8') as f:
                servers = json.load(f)

            for server in servers:
                if server.get('name') == name:
                    return server

            return None
        except Exception as e:
            raise Exception(f"读取通知服务商配置失败: {str(e)}")

    @staticmethod
    async def _send_chuanxi(server_config: Dict[str, str], key: str, content: str, msg: str, group_id: str = None) -> \
    Dict[str, Any]:
        """发送传息通知"""
        server_url = server_config.get('server')

        # 传息通知的payload格式
        payload = {
            "appkey": key,
            "title": content,
            "content": msg
        }

        # 添加可选的group_id参数
        if group_id:
            payload["group_id"] = group_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                server_url,
                json=payload,
                timeout=5
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"传息通知发送失败: {response.status_code} - {response.text}")

    @staticmethod
    async def _send_wechat_work(server_config: Dict[str, str], key: str, content: str, msg: str) -> Dict[str, Any]:
        """发送企业微信通知"""
        server_url = server_config.get('server')

        # 企业微信webhook格式 - 将key作为webhook的一部分
        full_url = f"{server_url}{key}"

        payload = {
            "msgtype": "text",
            "text": {
                "content": f"{content}\n{msg}"
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                full_url,
                json=payload,
                timeout=5.0
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "企业微信通知发送成功",
                    "data": response.json()
                }
            else:
                raise Exception(f"企业微信通知发送失败: {response.status_code} - {response.text}")

    @staticmethod
    async def _send_telegram(server_config: Dict[str, str], key: str, content: str, msg: str, chat_id: str = None) -> Dict[str, Any]:
        """发送Telegram消息"""
        try:
            if not chat_id:
                return {
                    "success": False,
                    "message": "Chat ID不能为空"
                }
            
            # 验证bot token - 使用传入的key参数而不是server_config中的token
            bot_token = key
            if not bot_token:
                return {
                    "success": False,
                    "message": "Telegram Bot Token不能为空"
                }
            
            # 使用python-telegram-bot发送消息
            bot = Bot(token=bot_token)
            async with bot:
                await bot.send_message(
                    text=msg,
                    chat_id=chat_id
                )
            
            return {
                "success": True,
                "message": "Telegram消息发送成功"
            }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"发送Telegram消息失败: {str(e)}"
            }

    @staticmethod
    async def _send_generic(server_config: Dict[str, str], key: str, content: str, msg: str) -> Dict[str, Any]:
        """通用发送方法"""
        server_url = server_config.get('server')

        payload = {
            "appkey": key,
            "content": content,
            "message": msg,
            "channel": server_config.get('name')
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                server_url,
                json=payload,
                timeout=5.0
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"{server_config.get('name')}通知发送成功",
                    "data": response.json()
                }
            else:
                raise Exception(f"{server_config.get('name')}通知发送失败: {response.status_code} - {response.text}")

