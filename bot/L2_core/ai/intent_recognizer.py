# L2_core/ai AI 意圖識別
# 建立日期：2025-12-24

"""
AI 意圖識別模組

使用 Gemini AI 判斷使用者意圖
"""

import os
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class IntentResult:
    """意圖識別結果"""
    intent: str              # 意圖名稱
    confidence: float        # 信心分數 (0-1)
    entities: Dict[str, Any] # 提取的實體
    raw_response: str        # 原始回應


class IntentRecognizer:
    """
    AI 意圖識別器
    
    使用 Gemini AI 判斷使用者意圖
    """
    
    # 支援的意圖
    INTENTS = {
        'same_day_booking': '當日預訂',
        'order_query': '訂單查詢',
        'room_availability': '房況查詢',
        'vip_service': 'VIP 服務',
        'general_question': '一般問題',
        'greeting': '打招呼',
        'cancel': '取消',
        'confirm': '確認',
        'unknown': '未知意圖'
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', '')
        self._model = None
    
    def _init_model(self):
        """初始化 Gemini 模型"""
        if self._model is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel('gemini-2.0-flash-exp')
            except ImportError:
                raise ImportError("請安裝 google-generativeai: pip install google-generativeai")
    
    def recognize(self, text: str, context: str = "") -> IntentResult:
        """
        識別使用者意圖
        
        Args:
            text: 使用者輸入
            context: 對話上下文
        
        Returns:
            IntentResult: 意圖識別結果
        """
        self._init_model()
        
        prompt = f"""你是一個飯店客服 AI，請判斷使用者的意圖。

使用者說：{text}

可能的意圖：
1. same_day_booking - 想要當日訂房（例如：今天想訂房、我要訂一間雙人房）
2. order_query - 查詢已有的訂單（例如：查訂單、我有訂房、訂單狀態）
3. room_availability - 查詢房況（例如：今天還有房嗎、有空房嗎）
4. vip_service - VIP 服務（例如：我是 VIP、VIP 優惠）
5. general_question - 一般問題（例如：幾點退房、早餐時間）
6. greeting - 打招呼（例如：你好、嗨）
7. cancel - 取消操作（例如：取消、不要了、算了）
8. confirm - 確認操作（例如：確認、好、是的、沒問題）
9. unknown - 無法判斷

請只回覆意圖名稱（如 same_day_booking），不要回覆其他內容。
如果可以提取到有用資訊（如房型、人數、日期），請用 JSON 格式回覆：
{{"intent": "意圖名稱", "room_type": "房型", "guests": 人數}}"""

        try:
            response = self._model.generate_content(prompt)
            result_text = response.text.strip()
            
            # 嘗試解析 JSON
            if result_text.startswith('{'):
                import json
                data = json.loads(result_text)
                intent = data.get('intent', 'unknown')
                entities = {k: v for k, v in data.items() if k != 'intent'}
            else:
                intent = result_text.lower().replace(' ', '_')
                entities = {}
            
            # 驗證意圖
            if intent not in self.INTENTS:
                intent = 'unknown'
            
            return IntentResult(
                intent=intent,
                confidence=0.8,  # 簡化處理
                entities=entities,
                raw_response=result_text
            )
        except Exception as e:
            print(f"意圖識別失敗: {e}")
            return IntentResult(
                intent='unknown',
                confidence=0,
                entities={},
                raw_response=str(e)
            )
    
    def recognize_simple(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        簡化版意圖識別（用於快速判斷）
        
        Returns:
            (intent, entities)
        """
        text_lower = text.lower()
        
        # 關鍵字匹配（快速路徑）
        if any(kw in text_lower for kw in ['訂房', '訂一間', '想訂', '要訂']):
            return 'same_day_booking', {}
        
        if any(kw in text_lower for kw in ['查訂單', '我有訂', '訂單', '預訂']):
            return 'order_query', {}
        
        if any(kw in text_lower for kw in ['還有房', '空房', '房況']):
            return 'room_availability', {}
        
        if any(kw in text_lower for kw in ['取消', '不要', '算了']):
            return 'cancel', {}
        
        if any(kw in text_lower for kw in ['確認', '好', '是', '沒問題', '對']):
            return 'confirm', {}
        
        if any(kw in text_lower for kw in ['你好', '嗨', 'hi', 'hello']):
            return 'greeting', {}
        
        # 無法快速判斷，使用 AI
        result = self.recognize(text)
        return result.intent, result.entities


# 全域意圖識別器
_recognizer = None

def get_recognizer() -> IntentRecognizer:
    """取得全域意圖識別器"""
    global _recognizer
    if _recognizer is None:
        _recognizer = IntentRecognizer()
    return _recognizer
