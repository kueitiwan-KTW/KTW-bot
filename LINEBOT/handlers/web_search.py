"""
網路搜尋模組
使用 Gemini 的 Search Grounding 功能進行網路搜尋
僅限內部 VIP 使用
"""

import os

# 嘗試使用新版 SDK (google-genai)，若失敗則用舊版
try:
    from google import genai
    from google.genai import types
    USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai_old
    USE_NEW_SDK = False


class WebSearchHandler:
    """網路搜尋處理器（使用 Google Search Grounding）"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        
        if USE_NEW_SDK and self.api_key:
            # 新版 SDK - 使用 Client 模式
            self.client = genai.Client(api_key=self.api_key)
        elif self.api_key:
            # 舊版 SDK
            genai_old.configure(api_key=self.api_key)
            self.client = None
    
    def search(self, query: str, user_name: str = "您") -> dict:
        """
        執行網路搜尋（使用 Gemini Search Grounding）
        
        Args:
            query: 搜尋關鍵字
            user_name: 用戶名稱（用於禮貌稱呼）
            
        Returns:
            dict: 搜尋結果
        """
        if not self.api_key:
            return {'success': False, 'message': '❌ 未設定 GOOGLE_API_KEY'}
        
        # 構建搜尋提示 - 內部 VIP 專屬 persona（有禮貌、簡潔）
        prompt = f"""你是龜地灣旅館的內部助理，正在為管理層人員 {user_name} 查詢資訊。

【查詢內容】{query}

【回覆要求】
1. 開頭用「{user_name}，」稱呼
2. 如果是餐廳/店家：優先提供電話、地址、營業時間
3. 如果是景點：優先提供開放時間、門票資訊
4. 請優先搜尋「屏東車城」「恆春」「墾丁」地區的資訊
5. 簡潔條列式回答，不要過於冗長
6. 如果資訊不確定，禮貌地建議致電確認
7. 最後可以加一句「還有其他需要幫忙的嗎？」

請用繁體中文回答。"""
        
        if USE_NEW_SDK:
            return self._search_with_new_sdk(prompt, user_name)
        else:
            return self._search_with_old_sdk(prompt, user_name)
    
    def _search_with_new_sdk(self, prompt: str, user_name: str) -> dict:
        """使用新版 SDK 進行搜尋（支援 Search Grounding）"""
        try:
            # 建立 Google Search 工具
            grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )
            
            config = types.GenerateContentConfig(
                tools=[grounding_tool]
            )
            
            # 使用 Gemini 3.0 Flash 進行搜尋
            response = self.client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt,
                config=config
            )
            
            if response and response.text:
                return {
                    'success': True,
                    'message': response.text
                }
            else:
                return {'success': False, 'message': '❌ 搜尋沒有回傳結果'}
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 新版 SDK 搜尋錯誤: {error_msg}")
            # Fallback 到舊版
            return self._search_with_old_sdk(prompt, user_name)
    
    def _search_with_old_sdk(self, prompt: str, user_name: str) -> dict:
        """使用舊版 SDK 進行搜尋（無 Search Grounding）"""
        try:
            model = genai_old.GenerativeModel('gemini-3-flash-preview')
            response = model.generate_content(prompt)
            
            if response and response.text:
                return {
                    'success': True,
                    'message': response.text
                }
            return {'success': False, 'message': '❌ 搜尋沒有回傳結果'}
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 舊版 SDK 搜尋錯誤: {error_msg}")
            return {'success': False, 'message': f'❌ 搜尋失敗: {error_msg}'}
    
    def search_weather(self, location: str = "墾丁") -> dict:
        """
        查詢天氣
        
        Args:
            location: 地點
            
        Returns:
            dict: 天氣資訊
        """
        return self.search(f"{location}今日天氣預報")
    
    def search_news(self, topic: str = "墾丁旅遊") -> dict:
        """
        查詢新聞
        
        Args:
            topic: 主題
            
        Returns:
            dict: 新聞資訊
        """
        return self.search(f"{topic} 最新新聞")


# 建立全域實例
web_search = WebSearchHandler()


# ============================================
# Function Calling 定義
# ============================================

WEB_SEARCH_FUNCTIONS = [
    {
        "name": "web_search",
        "description": "進行網路搜尋，查詢任何外部資訊。僅限內部 VIP 使用。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜尋關鍵字或問題"
                }
            },
            "required": ["query"]
        }
    }
]


def execute_web_search(function_name: str, arguments: dict) -> str:
    """
    執行網路搜尋 Function
    
    Args:
        function_name: 函數名稱
        arguments: 參數
        
    Returns:
        str: 搜尋結果
    """
    if function_name == "web_search":
        query = arguments.get('query', '')
        if not query:
            return "❌ 請提供搜尋關鍵字"
        result = web_search.search(query)
        return result.get('message', '搜尋完成')
    
    return f"❌ 未知的搜尋功能: {function_name}"
