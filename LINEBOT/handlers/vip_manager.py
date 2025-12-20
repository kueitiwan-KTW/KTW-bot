"""
VIP 用戶管理模組
雙層架構：
- guest: 客人 VIP（後台標籤識別）
- internal: 內部 VIP（董事長/管理層/員工，可存取完整功能）
"""

import requests
import os

class VIPManager:
    """VIP 用戶管理器"""
    
    def __init__(self, backend_url: str = None):
        """
        初始化 VIPManager
        
        Args:
            backend_url: Backend API URL，預設從環境變數讀取
        """
        self.backend_url = backend_url or os.getenv('KTW_BACKEND_URL', 'http://localhost:3000')
        self._cache = {}  # 簡單快取，減少 API 呼叫
    
    def get_vip_info(self, user_id: str) -> dict:
        """
        取得用戶 VIP 資訊
        
        Args:
            user_id: LINE User ID
            
        Returns:
            dict: VIP 資訊，包含 is_vip, vip_type, is_internal 等欄位
        """
        # 檢查快取
        if user_id in self._cache:
            return self._cache[user_id]
        
        try:
            response = requests.get(
                f"{self.backend_url}/api/vip/{user_id}",
                timeout=3
            )
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    'is_vip': data.get('is_vip', False),
                    'vip_type': data.get('vip_type'),  # 'guest' | 'internal' | None
                    'is_internal': data.get('is_internal', False),
                    'vip_level': data.get('data', {}).get('vip_level', 0) if data.get('data') else 0,
                    'role': data.get('data', {}).get('role') if data.get('data') else None,
                    'display_name': data.get('data', {}).get('display_name') if data.get('data') else None,
                    'permissions': data.get('data', {}).get('permissions', []) if data.get('data') else []
                }
                # 快取結果（5 分鐘過期由外部處理）
                self._cache[user_id] = result
                return result
            else:
                return self._default_result()
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ VIP 查詢失敗: {e}")
            return self._default_result()
    
    def is_vip(self, user_id: str) -> bool:
        """檢查用戶是否為 VIP（任何類型）"""
        info = self.get_vip_info(user_id)
        return info['is_vip']
    
    def is_internal(self, user_id: str) -> bool:
        """檢查用戶是否為內部 VIP（可存取完整功能）"""
        info = self.get_vip_info(user_id)
        return info['is_internal']
    
    def is_guest_vip(self, user_id: str) -> bool:
        """檢查用戶是否為客人 VIP"""
        info = self.get_vip_info(user_id)
        return info['is_vip'] and info['vip_type'] == 'guest'
    
    def get_vip_level(self, user_id: str) -> int:
        """取得 VIP 等級 (0=非VIP, 1-3=VIP等級)"""
        info = self.get_vip_info(user_id)
        return info['vip_level'] if info['is_vip'] else 0
    
    def get_role(self, user_id: str) -> str:
        """取得內部 VIP 角色 (chairman/manager/staff)"""
        info = self.get_vip_info(user_id)
        return info['role']
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """
        檢查用戶是否有特定權限
        
        Args:
            user_id: LINE User ID
            permission: 權限名稱，如 'query_revenue', 'web_search'
        """
        info = self.get_vip_info(user_id)
        
        # 內部 VIP 預設有所有權限
        if info['is_internal']:
            return True
        
        # 檢查明確授權
        return permission in info.get('permissions', [])
    
    def clear_cache(self, user_id: str = None):
        """
        清除快取
        
        Args:
            user_id: 指定用戶 ID，若為 None 則清除全部
        """
        if user_id:
            self._cache.pop(user_id, None)
        else:
            self._cache.clear()
    
    def _default_result(self) -> dict:
        """回傳預設結果（非 VIP）"""
        return {
            'is_vip': False,
            'vip_type': None,
            'is_internal': False,
            'vip_level': 0,
            'role': None,
            'display_name': None,
            'permissions': []
        }


# 建立全域實例供其他模組使用
vip_manager = VIPManager()
