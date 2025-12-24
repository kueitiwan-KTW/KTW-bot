# L1_adapters 基礎適配器
# 建立日期：2025-12-24

"""
統一訊息格式與平台適配器

設計原則：核心邏輯層不關心平台差異，Adapter 負責格式轉換
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


@dataclass
class UnifiedMessage:
    """統一訊息格式（跨平台）"""
    text: str = ""
    images: List[str] = field(default_factory=list)
    buttons: List[Dict[str, str]] = field(default_factory=list)
    quick_replies: List[str] = field(default_factory=list)
    
    # 平台專屬資料（可選）
    platform_data: Optional[Dict[str, Any]] = None


@dataclass
class UnifiedEvent:
    """統一事件格式（跨平台）"""
    user_id: str
    message_type: str  # text, image, audio, etc.
    content: str
    platform: str  # line, whatsapp, web
    
    # 原始事件（可選）
    raw_event: Optional[Dict[str, Any]] = None


class BaseAdapter(ABC):
    """
    平台適配器基類
    
    所有平台適配器需實現以下方法
    """
    
    @abstractmethod
    def parse_event(self, raw_event: Any) -> UnifiedEvent:
        """將平台事件轉換為統一格式"""
        pass
    
    @abstractmethod
    def to_platform(self, message: UnifiedMessage) -> Any:
        """將統一訊息轉換為平台格式"""
        pass
    
    @abstractmethod
    def send_message(self, user_id: str, message: UnifiedMessage) -> bool:
        """發送訊息到平台"""
        pass
    
    @abstractmethod
    def send_push(self, user_id: str, message: UnifiedMessage) -> bool:
        """主動推送訊息（用於 Triggers）"""
        pass
