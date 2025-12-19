"""
統一對話狀態機 (Unified Conversation State Machine)

職責：
- 管理所有用戶的對話狀態
- 提供統一的狀態轉換 API
- 處理跨流程意圖跳轉 (pending_intent)
- 根據狀態決定應使用的 Handler

設計原則：
- Single Source of Truth (SSOT)
- 所有狀態儲存在此類別中
- Handler 只負責業務邏輯，不管理狀態
"""

from typing import Dict, Optional, Any
from datetime import datetime


class ConversationStateMachine:
    """統一對話狀態機"""
    
    # 狀態定義
    STATE_IDLE = 'idle'
    
    # 訂單查詢流程狀態
    STATE_ORDER_QUERY_CONFIRMING = 'order_query.confirming'
    STATE_ORDER_QUERY_COLLECTING_PHONE = 'order_query.collecting_phone'
    STATE_ORDER_QUERY_COLLECTING_ARRIVAL = 'order_query.collecting_arrival'
    STATE_ORDER_QUERY_COLLECTING_SPECIAL = 'order_query.collecting_special'
    STATE_ORDER_QUERY_COMPLETED = 'order_query.completed'
    
    # 當日預訂流程狀態
    STATE_BOOKING_ASK_DATE = 'booking.ask_date'
    STATE_BOOKING_SHOW_ROOMS = 'booking.show_rooms'
    STATE_BOOKING_COLLECT_ROOM = 'booking.collect_room'
    STATE_BOOKING_COLLECT_COUNT = 'booking.collect_count'
    STATE_BOOKING_COLLECT_BED = 'booking.collect_bed'
    STATE_BOOKING_COLLECT_NAME = 'booking.collect_name'
    STATE_BOOKING_COLLECT_PHONE = 'booking.collect_phone'
    STATE_BOOKING_COLLECT_ARRIVAL = 'booking.collect_arrival'
    STATE_BOOKING_COLLECT_SPECIAL = 'booking.collect_special'
    STATE_BOOKING_CONFIRM = 'booking.confirm'
    STATE_BOOKING_COMPLETED = 'booking.completed'
    
    def __init__(self):
        """初始化狀態機"""
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_session(self, user_id: str) -> Dict[str, Any]:
        """
        取得或建立用戶 session
        
        Args:
            user_id: LINE 用戶 ID
            
        Returns:
            用戶的 session dict
        """
        if user_id not in self.sessions:
            self.sessions[user_id] = self._create_default_session()
        return self.sessions[user_id]
    
    def _create_default_session(self) -> Dict[str, Any]:
        """建立預設 session"""
        return {
            'state': self.STATE_IDLE,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'data': {},  # 流程相關資料
            'pending_intent': None,  # 待處理意圖
        }
    
    def get_state(self, user_id: str) -> str:
        """
        取得當前狀態
        
        Args:
            user_id: LINE 用戶 ID
            
        Returns:
            當前狀態字串
        """
        session = self.get_session(user_id)
        return session['state']
    
    def transition(self, user_id: str, target_state: str, data: Optional[Dict] = None):
        """
        狀態轉換
        
        Args:
            user_id: LINE 用戶 ID
            target_state: 目標狀態
            data: 可選的資料更新
        """
        session = self.get_session(user_id)
        old_state = session['state']
        session['state'] = target_state
        session['updated_at'] = datetime.now().isoformat()
        
        # 更新資料
        if data:
            session['data'].update(data)
        
        print(f"🔄 State Transition [{user_id}]: {old_state} → {target_state}")
    
    def get_data(self, user_id: str, key: str = None) -> Any:
        """
        取得 session 資料
        
        Args:
            user_id: LINE 用戶 ID
            key: 資料鍵名，None 表示取得整個 data dict
            
        Returns:
            資料值或整個 data dict
        """
        session = self.get_session(user_id)
        if key is None:
            return session['data']
        return session['data'].get(key)
    
    def set_data(self, user_id: str, key: str, value: Any):
        """
        設定 session 資料
        
        Args:
            user_id: LINE 用戶 ID
            key: 資料鍵名
            value: 資料值
        """
        session = self.get_session(user_id)
        session['data'][key] = value
        session['updated_at'] = datetime.now().isoformat()
    
    def get_active_handler_type(self, user_id: str) -> str:
        """
        根據狀態返回應使用的 Handler 類型
        
        Args:
            user_id: LINE 用戶 ID
            
        Returns:
            'order_query', 'same_day_booking', 或 'ai_conversation'
        """
        state = self.get_state(user_id)
        
        if state.startswith('order_query'):
            return 'order_query'
        elif state.startswith('booking'):
            return 'same_day_booking'
        else:
            return 'ai_conversation'
    
    def set_pending_intent(self, user_id: str, intent: str, message: Optional[str] = None):
        """
        設定待處理意圖 (跨流程跳轉)
        
        使用場景：
        - 用戶在「訂單查詢」中說「我要加訂」→ 設定 pending_intent='same_day_booking'
        - 用戶在「當日預訂」中說「我要查訂單」→ 設定 pending_intent='order_query'
        
        Args:
            user_id: LINE 用戶 ID
            intent: 意圖類型 ('same_day_booking' 或 'order_query')
            message: 可選的觸發訊息
        """
        session = self.get_session(user_id)
        session['pending_intent'] = intent
        if message:
            session['pending_intent_message'] = message
        session['updated_at'] = datetime.now().isoformat()
        print(f"📌 Pending Intent Set [{user_id}]: {intent}")
    
    def get_pending_intent(self, user_id: str) -> Optional[str]:
        """
        取得待處理意圖
        
        Args:
            user_id: LINE 用戶 ID
            
        Returns:
            pending_intent 字串，None 表示無待處理意圖
        """
        session = self.get_session(user_id)
        return session.get('pending_intent')
    
    def clear_pending_intent(self, user_id: str):
        """
        清除待處理意圖
        
        Args:
            user_id: LINE 用戶 ID
        """
        session = self.get_session(user_id)
        if 'pending_intent' in session:
            del session['pending_intent']
        if 'pending_intent_message' in session:
            del session['pending_intent_message']
        session['updated_at'] = datetime.now().isoformat()
        print(f"🧹 Pending Intent Cleared [{user_id}]")
    
    def execute_pending_intent(self, user_id: str) -> Optional[str]:
        """
        執行待處理意圖（流程完成後自動跳轉）
        
        Args:
            user_id: LINE 用戶 ID
            
        Returns:
            目標狀態字串，None 表示無待處理意圖
        """
        pending = self.get_pending_intent(user_id)
        if not pending:
            return None
        
        # 清除 pending_intent
        self.clear_pending_intent(user_id)
        
        # 根據意圖返回目標狀態
        intent_to_state = {
            'same_day_booking': self.STATE_BOOKING_ASK_DATE,
            'order_query': self.STATE_IDLE  # 需要用戶提供訂單號，所以回到 idle
        }
        
        target_state = intent_to_state.get(pending)
        print(f"🎯 Executing Pending Intent [{user_id}]: {pending} → {target_state}")
        return target_state
    
    def reset_session(self, user_id: str):
        """
        重置用戶 session
        
        Args:
            user_id: LINE 用戶 ID
        """
        if user_id in self.sessions:
            del self.sessions[user_id]
        print(f"🔄 Session Reset [{user_id}]")
    
    def is_in_active_flow(self, user_id: str) -> bool:
        """
        檢查用戶是否在進行中的流程
        
        Args:
            user_id: LINE 用戶 ID
            
        Returns:
            True 如果在進行中流程，False 如果閒置
        """
        state = self.get_state(user_id)
        return state != self.STATE_IDLE
