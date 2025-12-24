# L2_core/specs 規格定義
# 建立日期：2025-12-24

"""
規格定義

定義 capabilities 和 plugins 之間的契約。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


# === Schedule Spec ===

class ScheduleType(Enum):
    """排程類型"""
    CRON = "cron"        # 定時排程
    RUN_AT = "run_at"    # 指定時間
    DELAY = "delay"      # 延遲執行


@dataclass
class ScheduleSpec:
    """
    排程規格
    
    capabilities 產出此規格，L4_services/scheduler 執行。
    """
    job_id: str
    job_type: str              # reminder, review_check, publish
    tenant_id: str
    schedule_type: ScheduleType
    
    # 排程設定
    cron_expression: Optional[str] = None   # "0 9 * * *"
    run_at: Optional[str] = None            # ISO datetime
    delay_seconds: Optional[int] = None
    
    # 任務內容
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # 防重複
    idempotency_key: Optional[str] = None
    
    # 重試設定
    max_retries: int = 3
    retry_delay_seconds: int = 60


# === Publisher Spec ===

class PublishPlatform(Enum):
    """發佈平台"""
    LINE = "line"
    LINE_OA = "line_oa"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


@dataclass
class PublishSpec:
    """
    發佈規格
    
    capabilities 產出此規格，L4_services/publishers 執行。
    """
    platform: PublishPlatform
    tenant_id: str
    
    # 內容
    message: str
    images: List[str] = field(default_factory=list)
    
    # 目標
    target_user_id: Optional[str] = None  # 推送給特定用戶
    broadcast: bool = False               # 群發
    
    # 排程
    scheduled_at: Optional[str] = None


# === Trigger Spec ===

@dataclass
class TriggerSpec:
    """
    觸發規格
    
    plugins 定義此規格，capabilities 使用。
    """
    trigger_id: str
    trigger_type: str          # check_in_reminder, review_request
    condition: Dict[str, Any]  # 觸發條件
    template: str              # 訊息模板
    variables: List[str]       # 可用變數
