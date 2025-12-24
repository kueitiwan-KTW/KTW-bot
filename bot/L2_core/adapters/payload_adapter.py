# L2_core Payload 適配器
# 建立日期：2025-12-24

"""
Payload CMS API 適配器

用於從 Payload 讀取租戶配置，包括：
- 租戶資訊 (Tenants)
- 訂閱模組 (Subscriptions)
- 行業配置 (PluginConfigs)
- 觸發設定 (Triggers)
- 任務設定 (Tasks)
- 採集設定 (Collectors)
"""

from typing import Dict, Any, Optional, List
import json
import os


class PayloadAdapter:
    """Payload CMS API 適配器"""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.getenv('PAYLOAD_API_URL', 'http://localhost:3002/api')
        self.api_key = api_key or os.getenv('PAYLOAD_API_KEY', '')
    
    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """取得租戶資訊"""
        # TODO: 實現 API 呼叫
        # 目前回傳模擬資料
        return {
            'tenantId': tenant_id,
            'name': 'KTW Hotel',
            'industry': 'hotel',
            'isActive': True
        }
    
    def get_subscription(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """取得租戶訂閱資訊"""
        # TODO: 實現 API 呼叫
        return {
            'tenant': tenant_id,
            'plan': 'pro',
            'modules': ['event_triggers', 'review_management'],
            'status': 'active'
        }
    
    def get_plugin_config(self, tenant_id: str, plugin_type: str) -> Optional[Dict[str, Any]]:
        """取得行業插件配置"""
        # TODO: 實現 API 呼叫
        return None
    
    def get_triggers(self, tenant_id: str) -> List[Dict[str, Any]]:
        """取得事件觸發設定"""
        # TODO: 實現 API 呼叫
        return []
    
    def get_tasks(self, tenant_id: str) -> List[Dict[str, Any]]:
        """取得定時任務設定"""
        # TODO: 實現 API 呼叫
        return []
    
    def get_collectors(self, tenant_id: str) -> List[Dict[str, Any]]:
        """取得資訊採集設定"""
        # TODO: 實現 API 呼叫
        return []
    
    def get_prompts(self, tenant_id: str) -> Dict[str, str]:
        """取得 AI 提示詞"""
        # TODO: 實現 API 呼叫
        return {}
    
    def get_messages(self, tenant_id: str) -> Dict[str, str]:
        """取得訊息模板"""
        # TODO: 實現 API 呼叫
        return {}


def check_module_access(tenant_id: str, module_name: str) -> tuple[bool, Optional[str]]:
    """
    檢查租戶是否有訂閱該模組
    
    用法：
    @require_module('review_management')
    def handle_google_review():
        ...
    """
    adapter = PayloadAdapter()
    subscription = adapter.get_subscription(tenant_id)
    
    if not subscription:
        return False, "無法取得訂閱資訊"
    
    if subscription.get('status') != 'active':
        return False, "訂閱已過期，請續費"
    
    if module_name not in subscription.get('modules', []):
        MODULE_NAMES = {
            'event_triggers': '事件觸發包',
            'review_management': '評論管理包',
            'local_info': '在地資訊包',
            'multi_language': '多語言包',
            'advanced_ai': '進階 AI 包',
            'multi_platform': '跨平台包',
            'internal_ops': '內部營運包'
        }
        module_display = MODULE_NAMES.get(module_name, module_name)
        return False, f"此功能需要訂閱「{module_display}」"
    
    return True, None


def require_module(module_name: str):
    """
    模組權限檢查裝飾器
    
    用法：
    @require_module('review_management')
    def handle_google_review(tenant_id: str):
        ...
    """
    def decorator(func):
        def wrapper(tenant_id: str, *args, **kwargs):
            allowed, error_msg = check_module_access(tenant_id, module_name)
            if not allowed:
                return {'error': error_msg}
            return func(tenant_id, *args, **kwargs)
        return wrapper
    return decorator
