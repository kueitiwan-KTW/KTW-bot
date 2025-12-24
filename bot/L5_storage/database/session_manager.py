# L5_storage/database Session 管理
# 建立日期：2025-12-24

"""
Session 管理器

提供：
- 對話狀態持久化
- 狀態機序列化/反序列化
- 支援 SQLite（開發）和 Redis（正式）
"""

import json
import sqlite3
import os
from typing import Optional, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod


class BaseSessionStore(ABC):
    """Session 儲存基類"""
    
    @abstractmethod
    def get(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """取得 Session"""
        pass
    
    @abstractmethod
    def set(self, user_id: str, tenant_id: str, data: Dict[str, Any]) -> bool:
        """儲存 Session"""
        pass
    
    @abstractmethod
    def delete(self, user_id: str, tenant_id: str) -> bool:
        """刪除 Session"""
        pass


class SQLiteSessionStore(BaseSessionStore):
    """
    SQLite Session 儲存
    
    適用於開發和單機部署
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), 
            '..', '..', '..', 'data', 'sessions.db'
        )
        self._init_db()
    
    def _init_db(self):
        """初始化資料庫"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                user_id TEXT,
                tenant_id TEXT,
                data TEXT,
                created_at TEXT,
                updated_at TEXT,
                PRIMARY KEY (user_id, tenant_id)
            )
        ''')
        conn.commit()
        conn.close()
    
    def get(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """取得 Session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT data FROM sessions WHERE user_id = ? AND tenant_id = ?',
            (user_id, tenant_id)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def set(self, user_id: str, tenant_id: str, data: Dict[str, Any]) -> bool:
        """儲存 Session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        data_json = json.dumps(data, ensure_ascii=False)
        
        cursor.execute('''
            INSERT OR REPLACE INTO sessions (user_id, tenant_id, data, created_at, updated_at)
            VALUES (?, ?, ?, COALESCE((SELECT created_at FROM sessions WHERE user_id = ? AND tenant_id = ?), ?), ?)
        ''', (user_id, tenant_id, data_json, user_id, tenant_id, now, now))
        
        conn.commit()
        conn.close()
        return True
    
    def delete(self, user_id: str, tenant_id: str) -> bool:
        """刪除 Session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM sessions WHERE user_id = ? AND tenant_id = ?',
            (user_id, tenant_id)
        )
        conn.commit()
        conn.close()
        return True


class SessionManager:
    """
    Session 管理器
    
    用法：
    session = SessionManager()
    session.save_machine(user_id, tenant_id, machine)
    machine = session.load_machine(user_id, tenant_id, MachineClass)
    """
    
    def __init__(self, store: BaseSessionStore = None):
        self.store = store or SQLiteSessionStore()
    
    def get(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """取得 Session 資料"""
        return self.store.get(user_id, tenant_id)
    
    def save(self, user_id: str, tenant_id: str, data: Dict[str, Any]) -> bool:
        """儲存 Session 資料"""
        return self.store.set(user_id, tenant_id, data)
    
    def delete(self, user_id: str, tenant_id: str) -> bool:
        """刪除 Session"""
        return self.store.delete(user_id, tenant_id)
    
    def save_machine(self, user_id: str, tenant_id: str, machine: Any) -> bool:
        """
        儲存狀態機
        
        狀態機需要實現 to_dict() 方法
        """
        if hasattr(machine, 'to_dict'):
            data = machine.to_dict()
            data['machine_type'] = machine.__class__.__name__
            return self.save(user_id, tenant_id, data)
        return False
    
    def load_machine(self, user_id: str, tenant_id: str, machine_classes: Dict[str, type]) -> Optional[Any]:
        """
        載入狀態機
        
        Args:
            user_id: 使用者 ID
            tenant_id: 租戶 ID
            machine_classes: 狀態機類別對照表 {'SameDayBookingMachine': SameDayBookingMachine}
        
        Returns:
            狀態機實例，或 None
        """
        data = self.get(user_id, tenant_id)
        if not data:
            return None
        
        machine_type = data.get('machine_type')
        if machine_type and machine_type in machine_classes:
            machine_class = machine_classes[machine_type]
            if hasattr(machine_class, 'from_dict'):
                return machine_class.from_dict(data)
        
        return None
    
    def clear_machine(self, user_id: str, tenant_id: str) -> bool:
        """清除狀態機（重置對話）"""
        return self.delete(user_id, tenant_id)


# 全域 Session 管理器實例
_session_manager = None

def get_session_manager() -> SessionManager:
    """取得全域 Session 管理器"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
