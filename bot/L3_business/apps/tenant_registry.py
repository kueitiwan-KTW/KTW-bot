# L3_business/apps/tenant_registry.py
# 建立日期：2025-12-25

"""
Tenant Registry（租戶註冊中心）

職責：
- 管理多租戶配置
- 整合 Payload CMS 設定
- 提供模組啟用控制

這是 Bot 的多租戶控制中心。
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# 嘗試導入 Payload Client
try:
    from L5_storage.api.payload_client import (
        PayloadClient, TenantConfig, SubscriptionConfig, get_payload_client
    )
    PAYLOAD_AVAILABLE = True
except ImportError:
    PAYLOAD_AVAILABLE = False


@dataclass
class TenantRuntime:
    """租戶運行時配置"""
    tenant_id: str
    name: str
    
    # Payload 配置
    payload_config: Optional[Any] = None
    subscription: Optional[Any] = None
    
    # LINE 設定
    line_channel_access_token: Optional[str] = None
    line_channel_secret: Optional[str] = None
    
    # 模組啟用狀態
    enabled_modules: List[str] = field(default_factory=list)
    
    # 本地覆寫（可選）
    local_overrides: Dict[str, Any] = field(default_factory=dict)


class TenantRegistry:
    """
    租戶註冊中心
    
    功能：
    - 啟動時從 Payload 載入租戶配置
    - 快取租戶設定
    - 提供模組啟用控制
    """
    
    def __init__(self):
        self.tenants: Dict[str, TenantRuntime] = {}
        self.payload_client = get_payload_client() if PAYLOAD_AVAILABLE else None
        self._initialized = False
    
    def initialize(self, tenant_ids: List[str] = None):
        """
        初始化租戶配置
        
        Args:
            tenant_ids: 要載入的租戶 ID 列表（空 = 載入環境變數指定的）
        """
        if not tenant_ids:
            # 從環境變數取得
            env_tenants = os.environ.get('BOT_TENANT_IDS', 'ktw_hotel')
            tenant_ids = [t.strip() for t in env_tenants.split(',')]
        
        print(f"🚀 初始化租戶: {tenant_ids}")
        
        for tenant_id in tenant_ids:
            self._load_tenant(tenant_id)
        
        self._initialized = True
        print(f"✅ 租戶初始化完成，共 {len(self.tenants)} 個租戶")
    
    def _load_tenant(self, tenant_id: str):
        """載入單一租戶"""
        runtime = TenantRuntime(
            tenant_id=tenant_id,
            name=tenant_id  # 預設名稱
        )
        
        # 從 Payload 載入
        if self.payload_client:
            config = self.payload_client.get_tenant(tenant_id)
            if config:
                runtime.name = config.name
                runtime.payload_config = config
                runtime.line_channel_access_token = config.line_channel_access_token
                runtime.line_channel_secret = config.line_channel_secret
                print(f"  📦 從 Payload 載入: {tenant_id} ({config.name})")
            
            # 載入訂閱
            sub = self.payload_client.get_subscription(tenant_id)
            if sub:
                runtime.subscription = sub
                runtime.enabled_modules = sub.modules
                print(f"  📋 訂閱: {sub.plan} ({len(sub.modules)} 模組)")
        
        # 載入本地覆寫（如果有）
        self._load_local_overrides(runtime)
        
        self.tenants[tenant_id] = runtime
    
    def _load_local_overrides(self, runtime: TenantRuntime):
        """載入本地覆寫配置"""
        import json
        config_path = f"tenants/{runtime.tenant_id}/config.json"
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    runtime.local_overrides = json.load(f)
                print(f"  🔧 載入本地覆寫: {config_path}")
        except Exception as e:
            pass  # 本地覆寫是可選的
    
    # === 查詢方法 ===
    
    def get_tenant(self, tenant_id: str) -> Optional[TenantRuntime]:
        """取得租戶運行時配置"""
        return self.tenants.get(tenant_id)
    
    def is_module_enabled(self, tenant_id: str, module_id: str) -> bool:
        """
        檢查模組是否啟用
        
        優先順序：
        1. 本地覆寫
        2. Payload 訂閱
        3. 預設禁用
        """
        runtime = self.get_tenant(tenant_id)
        if not runtime:
            return False
        
        # 檢查本地覆寫
        overrides = runtime.local_overrides.get('modules', {})
        if module_id in overrides:
            return overrides[module_id].get('enabled', False)
        
        # 檢查 Payload 訂閱
        return module_id in runtime.enabled_modules
    
    def get_line_config(self, tenant_id: str) -> Optional[Dict[str, str]]:
        """取得 LINE 設定"""
        runtime = self.get_tenant(tenant_id)
        if not runtime:
            return None
        
        # 優先使用 Payload 設定
        if runtime.line_channel_access_token:
            return {
                'channel_access_token': runtime.line_channel_access_token,
                'channel_secret': runtime.line_channel_secret
            }
        
        # 回退到環境變數（相容舊系統）
        return {
            'channel_access_token': os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'),
            'channel_secret': os.environ.get('LINE_CHANNEL_SECRET')
        }
    
    def get_enabled_modules(self, tenant_id: str) -> List[str]:
        """取得所有已啟用模組"""
        runtime = self.get_tenant(tenant_id)
        if not runtime:
            return []
        return runtime.enabled_modules
    
    def list_tenants(self) -> List[str]:
        """列出所有租戶"""
        return list(self.tenants.keys())


# 全域 Registry 實例
tenant_registry = TenantRegistry()


def get_tenant_registry() -> TenantRegistry:
    """取得 TenantRegistry 實例"""
    return tenant_registry
