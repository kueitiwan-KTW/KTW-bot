"""
意圖偵測器 (Intent Detector)

職責：
- 統一所有意圖偵測邏輯
- 避免各 Handler 重複實作
- 提供可測試、可維護的意圖識別

設計原則：
- 使用靜態方法 (Stateless)
- 關鍵字匹配為主，未來可擴充為 AI 判斷
"""

import re
from typing import List


class IntentDetector:
    """統一意圖偵測器"""
    
    @staticmethod
    def has_order_number(message: str) -> bool:
        """
        檢測訂單編號（排除電話號碼）
        
        邏輯：
        1. 排除 09 開頭的 10 位數字（電話號碼）
        2. 檢測不以 0 開頭的 5-10 位數字（訂單編號）
        
        Args:
            message: 用戶訊息
            
        Returns:
            True 如果包含訂單編號
        """
        # 排除電話號碼（09 開頭的 10 位數）
        if re.search(r'09\d{8}', message):
            return False
        
        # 訂單編號：不以 0 開頭的 5-10 位數字
        return bool(re.search(r'\b[1-9]\d{4,9}\b', message))
    
    @staticmethod
    def extract_order_number(message: str) -> str:
        """
        提取訂單編號
        
        Args:
            message: 用戶訊息
            
        Returns:
            訂單編號字串，None 表示未找到
        """
        # 排除電話號碼
        if re.search(r'09\d{8}', message):
            # 嘗試找到非電話的數字
            numbers = re.findall(r'\b[1-9]\d{4,9}\b', message)
            if numbers:
                return numbers[0]
            return None
        
        # 提取訂單編號
        match = re.search(r'\b[1-9]\d{4,9}\b', message)
        return match.group(0) if match else None
    
    @staticmethod
    def is_booking_intent(message: str) -> bool:
        """
        檢測訂房意圖
        
        Args:
            message: 用戶訊息
            
        Returns:
            True 如果是訂房意圖
        """
        keywords = [
            '訂房', '預訂', '今天住', '今日住', '有房', '還有房',
            '空房', '想住', '要住', '可以住', '今天訂', '今日訂',
            '今天', '今日', '明天', '明日',
            '加訂', '加定', '多訂', '再訂', '多一間', '再一間'
        ]
        return any(kw in message for kw in keywords)
    
    @staticmethod
    def is_same_day_booking_intent(message: str) -> bool:
        """
        檢測當日訂房意圖（強調「今天」）
        
        Args:
            message: 用戶訊息
            
        Returns:
            True 如果明確提到今天
        """
        keywords = ['今天', '今日', '今晚', '現在']
        return any(kw in message for kw in keywords)
    
    @staticmethod
    def is_query_intent(message: str) -> bool:
        """
        檢測查詢訂單意圖
        
        Args:
            message: 用戶訊息
            
        Returns:
            True 如果是查詢意圖
        """
        keywords = [
            '查訂單', '查詢訂單', '我有訂', '確認訂單', '我的訂單',
            '我訂了', '已經訂', '訂單狀態', '訂單資訊'
        ]
        return any(kw in message for kw in keywords)
    
    @staticmethod
    def is_cancel_intent(message: str) -> bool:
        """
        檢測取消意圖
        
        Args:
            message: 用戶訊息
            
        Returns:
            True 如果是取消意圖
        """
        keywords = [
            '取消', '不要', '算了', '放棄', '不訂', '不定',
            '退訂', '退房', '取消訂房', '取消預訂'
        ]
        return any(kw in message for kw in keywords)
    
    @staticmethod
    def is_interrupt_intent(message: str) -> bool:
        """
        檢測中斷流程意圖
        
        Args:
            message: 用戶訊息
            
        Returns:
            True 如果用戶想中斷當前流程
        """
        keywords = [
            '不要', '算了', '取消', '停止', '退出',
            '重新開始', '重來', 'reset', 'restart'
        ]
        return any(kw in message for kw in keywords)
    
    @staticmethod
    def is_confirmation(message: str) -> bool:
        """
        檢測確認意圖（是/對/沒錯）
        
        Args:
            message: 用戶訊息
            
        Returns:
            True 如果是確認
        """
        keywords = [
            '是', '對', '沒錯', '正確', '確認', 'yes', '好', 'ok', 'OK', 'Yes'
        ]
        # 完全匹配或包含在短訊息中
        message_lower = message.lower().strip()
        return message_lower in keywords or any(kw in message and len(message) <= 10 for kw in keywords)
    
    @staticmethod
    def is_rejection(message: str) -> bool:
        """
        檢測否定意圖（不是/錯了）
        
        Args:
            message: 用戶訊息
            
        Returns:
            True 如果是否定
        """
        keywords = [
            '不是', '錯', '不對', '不正確', 'no', 'No', 'NO'
        ]
        message_lower = message.lower().strip()
        return message_lower in keywords or any(kw in message and len(message) <= 10 for kw in keywords)
    
    @staticmethod
    def extract_phone_number(message: str) -> str:
        """
        提取電話號碼
        
        Args:
            message: 用戶訊息
            
        Returns:
            電話號碼字串，None 表示未找到
        """
        # 台灣手機號碼格式：09 開頭的 10 位數字
        match = re.search(r'09\d{8}', message)
        return match.group(0) if match else None
