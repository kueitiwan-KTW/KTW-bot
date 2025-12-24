# L5_storage/api/payload_client.py
# 建立日期：2025-12-25

"""
Payload CMS API Client

職責：
- 讀取租戶設定
- 讀取訂閱/模組列表
- 讀取提醒設定

這是 Bot 與 Payload CMS 的橋樑。
"""

import os
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class TenantConfig:
    """租戶設定"""
    tenant_id: str
    name: str
    industry: str
    status: str
    
    # LINE 設定（從 channels 取第一個 LINE）
    line_channel_access_token: Optional[str] = None
    line_channel_secret: Optional[str] = None
    line_webhook_url: Optional[str] = None
    line_enabled: bool = False


@dataclass
class SubscriptionConfig:
    """訂閱設定"""
    plan: str  # free / basic / pro / enterprise
    modules: List[str]  # 已啟用的模組
    status: str  # active / expired / cancelled


class PayloadClient:
    """
    Payload CMS API Client
    
    功能：
    - 讀取租戶設定
    - 讀取訂閱模組
    - 快取設定避免重複請求
    """
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.environ.get('PAYLOAD_API_URL', 'http://localhost:3002')
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 分鐘快取
    
    # === 租戶設定 ===
    
    def get_tenant(self, tenant_id: str) -> Optional[TenantConfig]:
        """
        取得租戶設定
        
        Args:
            tenant_id: 租戶 ID（如 ktw_hotel）
            
        Returns:
            TenantConfig 或 None
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tenants",
                params={"where[tenantId][equals]": tenant_id},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('docs'):
                print(f"⚠️ 找不到租戶: {tenant_id}")
                return None
            
            tenant = data['docs'][0]
            
            # 解析 LINE 設定（從 channels 陣列）
            line_config = self._extract_line_config(tenant.get('channels', []))
            
            return TenantConfig(
                tenant_id=tenant.get('tenantId'),
                name=tenant.get('name'),
                industry=tenant.get('industry'),
                status=tenant.get('status'),
                line_channel_access_token=line_config.get('channelAccessToken'),
                line_channel_secret=line_config.get('channelSecret'),
                line_webhook_url=line_config.get('webhookUrl'),
                line_enabled=line_config.get('enabled', False)
            )
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Payload API 錯誤: {e}")
            return None
    
    def _extract_line_config(self, channels: List[Dict]) -> Dict[str, Any]:
        """從 channels 陣列提取 LINE 設定"""
        for channel in channels:
            if channel.get('platform') == 'line' and channel.get('enabled'):
                return channel
        return {}
    
    # === 訂閱設定 ===
    
    def get_subscription(self, tenant_id: str) -> Optional[SubscriptionConfig]:
        """
        取得租戶訂閱設定
        
        Args:
            tenant_id: 租戶 ID
            
        Returns:
            SubscriptionConfig 或 None
        """
        try:
            # 先取得租戶 ID（Payload 內部 ID）
            tenant = self._get_tenant_internal_id(tenant_id)
            if not tenant:
                return None
            
            response = requests.get(
                f"{self.base_url}/api/subscriptions",
                params={
                    "where[tenant][equals]": tenant['id'],
                    "where[status][equals]": "active"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('docs'):
                print(f"⚠️ 找不到訂閱: {tenant_id}")
                return None
            
            sub = data['docs'][0]
            
            return SubscriptionConfig(
                plan=sub.get('plan', 'free'),
                modules=sub.get('modules', []),
                status=sub.get('status', 'active')
            )
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Payload API 錯誤: {e}")
            return None
    
    def _get_tenant_internal_id(self, tenant_id: str) -> Optional[Dict]:
        """取得租戶內部 ID"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tenants",
                params={"where[tenantId][equals]": tenant_id},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('docs'):
                return data['docs'][0]
            return None
            
        except:
            return None
    
    # === 便利方法 ===
    
    def is_module_enabled(self, tenant_id: str, module_id: str) -> bool:
        """
        檢查模組是否啟用
        
        Args:
            tenant_id: 租戶 ID
            module_id: 模組 ID（如 order_query, check_in_reminder）
            
        Returns:
            True 啟用，False 未啟用
        """
        sub = self.get_subscription(tenant_id)
        if not sub:
            return False
        return module_id in sub.modules
    
    def get_enabled_modules(self, tenant_id: str) -> List[str]:
        """取得所有已啟用模組"""
        sub = self.get_subscription(tenant_id)
        if not sub:
            return []
        return sub.modules
    
    def get_line_config(self, tenant_id: str) -> Optional[Dict[str, str]]:
        """取得 LINE 設定（快捷方法）"""
        tenant = self.get_tenant(tenant_id)
        if not tenant or not tenant.line_enabled:
            return None
        return {
            'channel_access_token': tenant.line_channel_access_token,
            'channel_secret': tenant.line_channel_secret,
            'webhook_url': tenant.line_webhook_url
        }


# 全域 Client 實例
payload_client = PayloadClient()


def get_payload_client() -> PayloadClient:
    """取得 Payload Client 實例"""
    return payload_client
