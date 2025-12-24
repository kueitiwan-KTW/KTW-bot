# L2_core 基礎狀態機
# 建立日期：2025-12-24

"""
基礎狀態機類別

所有狀態機的父類，提供：
- 序列化/反序列化（用於 Session 持久化）
- 通用事件監聽
- 錯誤處理
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime

# 備註：正式使用時需安裝 python-statemachine
# pip install python-statemachine

@dataclass
class BaseModel:
    """基礎資料模型"""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化為 dict"""
        data = asdict(self)
        # 轉換 datetime 為 ISO 格式
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """從 dict 反序列化"""
        # 轉換 ISO 格式為 datetime
        for key, value in data.items():
            if isinstance(value, str) and 'T' in value:
                try:
                    data[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
        return cls(**data)


class BaseMachine:
    """
    基礎狀態機類別
    
    使用 python-statemachine 時，繼承此類別：
    
    from statemachine import StateMachine, State
    
    class OrderQueryMachine(BaseMachine, StateMachine):
        idle = State(initial=True)
        confirming = State()
        ...
    """
    
    def __init__(self, model: Optional[BaseModel] = None, user_id: str = None, tenant_id: str = None):
        self.model = model
        self.user_id = user_id
        self.tenant_id = tenant_id
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化狀態機（用於 Session 持久化）"""
        return {
            'current_state': getattr(self, 'current_state', {}).get('id', 'idle') if hasattr(self, 'current_state') else 'idle',
            'model_data': self.model.to_dict() if self.model else {},
            'user_id': self.user_id,
            'tenant_id': self.tenant_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], model_class=None):
        """從 dict 恢復狀態機"""
        model = None
        if model_class and data.get('model_data'):
            model = model_class.from_dict(data['model_data'])
        
        machine = cls(
            model=model,
            user_id=data.get('user_id'),
            tenant_id=data.get('tenant_id')
        )
        
        # 恢復狀態（需要 python-statemachine 支援）
        # target_state = data.get('current_state', 'idle')
        # machine._set_current_state(target_state)
        
        return machine
    
    def on_error(self, error: Exception) -> str:
        """通用錯誤處理"""
        return "抱歉，我不太確定您的意思，可以再說一次嗎？"
