# L2_core/events 統一事件格式
# 建立日期：2025-12-24

"""
統一事件格式

所有平台的事件轉換為統一格式，狀態機只吃 Event。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class Event:
    """
    統一事件格式
    
    狀態機只吃 Event，不直接吃原始文字。
    """
    name: str              # 事件名稱：ORDER_QUERY_START, BOOKING_SET_PHONE
    slots: Dict[str, Any]  # 提取的欄位：{phone, arrival_time...}
    confidence: float      # AI 信心分數 (0-1)
    raw_text: str          # 原始輸入文字
    source: str            # 來源平台：line, whatsapp, web
    
    # 可選欄位
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# 常用事件名稱
class EventNames:
    """事件名稱常數"""
    
    # 訂房相關
    BOOKING_START = "BOOKING_START"
    BOOKING_SET_ROOM = "BOOKING_SET_ROOM"
    BOOKING_SET_PHONE = "BOOKING_SET_PHONE"
    BOOKING_SET_ARRIVAL = "BOOKING_SET_ARRIVAL"
    BOOKING_CONFIRM = "BOOKING_CONFIRM"
    BOOKING_CANCEL = "BOOKING_CANCEL"
    
    # 查詢相關
    ORDER_QUERY_START = "ORDER_QUERY_START"
    ORDER_QUERY_CONFIRM = "ORDER_QUERY_CONFIRM"
    
    # 通用
    GREETING = "GREETING"
    CANCEL = "CANCEL"
    CONFIRM = "CONFIRM"
    UNKNOWN = "UNKNOWN"
