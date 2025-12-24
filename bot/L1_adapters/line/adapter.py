# L1_adapters LINE 適配器
# 建立日期：2025-12-24

"""
LINE 平台適配器

將 LINE 事件轉換為統一格式，將統一訊息轉換為 LINE 格式
"""

from typing import Any, Optional, List, Dict
from dataclasses import dataclass
import os

from ..base_adapter import BaseAdapter, UnifiedMessage, UnifiedEvent


class LineAdapter(BaseAdapter):
    """
    LINE 平台適配器
    
    職責：
    1. 接收 LINE Webhook 事件
    2. 轉換為統一訊息格式
    3. 將回覆轉換為 LINE 格式
    4. 發送訊息
    """
    
    def __init__(self, channel_access_token: str = None, channel_secret: str = None):
        self.channel_access_token = channel_access_token or os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
        self.channel_secret = channel_secret or os.getenv('LINE_CHANNEL_SECRET', '')
        
        # 延遲導入 LINE SDK（避免未安裝時報錯）
        self._line_bot_api = None
        self._handler = None
    
    def _init_line_sdk(self):
        """初始化 LINE SDK"""
        if self._line_bot_api is None:
            try:
                from linebot import LineBotApi, WebhookHandler
                self._line_bot_api = LineBotApi(self.channel_access_token)
                self._handler = WebhookHandler(self.channel_secret)
            except ImportError:
                raise ImportError("請安裝 line-bot-sdk: pip install line-bot-sdk")
    
    def parse_event(self, raw_event: Any) -> UnifiedEvent:
        """
        將 LINE 事件轉換為統一格式
        
        Args:
            raw_event: LINE MessageEvent 物件
        
        Returns:
            UnifiedEvent: 統一事件格式
        """
        # 取得使用者 ID
        user_id = raw_event.source.user_id if hasattr(raw_event, 'source') else ''
        
        # 判斷訊息類型
        message = getattr(raw_event, 'message', None)
        if message is None:
            return UnifiedEvent(
                user_id=user_id,
                message_type='unknown',
                content='',
                platform='line',
                raw_event=raw_event
            )
        
        message_type = message.type if hasattr(message, 'type') else 'text'
        
        # 取得內容
        content = ''
        if message_type == 'text':
            content = message.text if hasattr(message, 'text') else ''
        elif message_type == 'image':
            content = message.id if hasattr(message, 'id') else ''
        elif message_type == 'audio':
            content = message.id if hasattr(message, 'id') else ''
        
        return UnifiedEvent(
            user_id=user_id,
            message_type=message_type,
            content=content,
            platform='line',
            raw_event=raw_event
        )
    
    def to_platform(self, message: UnifiedMessage) -> List[Any]:
        """
        將統一訊息轉換為 LINE 格式
        
        Args:
            message: UnifiedMessage 統一訊息
        
        Returns:
            list: LINE 訊息物件列表
        """
        from linebot.models import (
            TextSendMessage,
            ImageSendMessage,
            QuickReply,
            QuickReplyButton,
            MessageAction
        )
        
        messages = []
        
        # 文字訊息
        if message.text:
            text_msg = TextSendMessage(text=message.text)
            
            # 快速回覆
            if message.quick_replies:
                items = [
                    QuickReplyButton(action=MessageAction(label=qr[:20], text=qr))
                    for qr in message.quick_replies[:13]  # LINE 限制 13 個
                ]
                text_msg.quick_reply = QuickReply(items=items)
            
            messages.append(text_msg)
        
        # 圖片訊息
        for image_url in message.images:
            messages.append(ImageSendMessage(
                original_content_url=image_url,
                preview_image_url=image_url
            ))
        
        return messages
    
    def send_message(self, reply_token: str, message: UnifiedMessage) -> bool:
        """
        發送回覆訊息
        
        Args:
            reply_token: LINE reply token
            message: UnifiedMessage 統一訊息
        
        Returns:
            bool: 是否成功
        """
        self._init_line_sdk()
        
        try:
            line_messages = self.to_platform(message)
            self._line_bot_api.reply_message(reply_token, line_messages)
            return True
        except Exception as e:
            print(f"LINE 發送訊息失敗: {e}")
            return False
    
    def send_push(self, user_id: str, message: UnifiedMessage) -> bool:
        """
        主動推送訊息
        
        Args:
            user_id: LINE 使用者 ID
            message: UnifiedMessage 統一訊息
        
        Returns:
            bool: 是否成功
        """
        self._init_line_sdk()
        
        try:
            line_messages = self.to_platform(message)
            self._line_bot_api.push_message(user_id, line_messages)
            return True
        except Exception as e:
            print(f"LINE 推送訊息失敗: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        取得使用者資料
        
        Args:
            user_id: LINE 使用者 ID
        
        Returns:
            dict: 使用者資料（display_name, picture_url 等）
        """
        self._init_line_sdk()
        
        try:
            profile = self._line_bot_api.get_profile(user_id)
            return {
                'user_id': profile.user_id,
                'display_name': profile.display_name,
                'picture_url': profile.picture_url,
                'status_message': profile.status_message
            }
        except Exception as e:
            print(f"LINE 取得使用者資料失敗: {e}")
            return None
