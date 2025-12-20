"""
VIP 服務處理器
處理內部 VIP 和客人 VIP 的專屬功能

功能：
- 內部 VIP：PMS 查詢、網路搜尋、無限制 AI 對話、圖片分析
- 客人 VIP：（未來）專屬優惠、優先服務

特色：
- 支援上下文記憶（任務記憶）
- 統一入口管理所有 VIP 功能
"""

import os
import re
from typing import Optional, Dict, Any
from datetime import datetime
from PIL import Image
import io

from .base_handler import BaseHandler
from .vip_manager import vip_manager
from .internal_query import internal_query
from .web_search import web_search


class VIPServiceHandler(BaseHandler):
    """
    VIP 服務處理器
    
    狀態：
    - vip_idle: 閒置
    - vip_waiting_image: 等待圖片（記住任務）
    """
    
    # 狀態常數
    STATE_VIP_IDLE = 'vip_idle'
    STATE_VIP_WAITING_IMAGE = 'vip_waiting_image'
    
    # 角色稱謂對照表
    ROLE_TITLES = {
        'chairman': '董事長',
        'manager': '經理',
        'staff': '同事',
        'super_vip': '長官'
    }
    
    def __init__(self, state_machine, logger, vision_model=None):
        """
        初始化 VIP 服務處理器
        
        Args:
            state_machine: 統一對話狀態機
            logger: 對話記錄器
            vision_model: Gemini Vision 模型（用於圖片辨識）
        """
        super().__init__()
        self.state_machine = state_machine
        self.logger = logger
        self.vision_model = vision_model
    
    def is_vip(self, user_id: str) -> bool:
        """檢查用戶是否為任何類型的 VIP"""
        return vip_manager.is_vip(user_id)
    
    def is_internal(self, user_id: str) -> bool:
        """檢查用戶是否為內部 VIP"""
        return vip_manager.is_internal(user_id)
    
    def is_active(self, user_id: str) -> bool:
        """檢查用戶是否在 VIP 服務流程中（有待處理任務）"""
        state = self.state_machine.get_state(user_id)
        return state.startswith('vip_')
    
    def get_role_title(self, user_id: str) -> str:
        """取得 VIP 角色稱謂"""
        vip_info = vip_manager.get_vip_info(user_id)
        role = vip_info.get('role') if vip_info else None
        return self.ROLE_TITLES.get(role, '長官')
    
    def handle_message(self, user_id: str, message: str, display_name: str = None) -> Optional[str]:
        """處理文字訊息 (重構版)"""
        # 只處理內部 VIP
        if not self.is_internal(user_id):
            return None
        
        role_title = self.get_role_title(user_id)
        state = self.state_machine.get_state(user_id)
        
        # 1. 處理狀態機任務 (等待圖片)
        if state == self.STATE_VIP_WAITING_IMAGE:
            # 用戶傳了文字而非圖片
            pending_task = self.state_machine.get_data(user_id, 'pending_task')
            desc = pending_task.get('description', '處理') if pending_task else '處理'
            return f"{role_title}，請傳送您要{desc}的圖片。"
        
        # 2. 偵測是否需要圖片的任務
        image_task = self._detect_image_task(message)
        if image_task:
            self.state_machine.transition(user_id, self.STATE_VIP_WAITING_IMAGE)
            self.state_machine.set_data(user_id, 'pending_task', image_task)
            return f"{role_title}，好的，請傳送您要{image_task['description']}的圖片。"
        
        # 3. 處理 PMS 業務查詢 (關鍵字驅動)
        pms_response = self._handle_pms_query(message, role_title)
        if pms_response:
            return pms_response
        
        # 4. 網路搜尋
        search_match = re.search(r'(?:幫我查一下|幫我查|搜尋一下|搜尋|查一下|上網查|幫我搜尋|幫查)(.+)', message)
        if search_match:
            query = search_match.group(1).strip()
            if query:
                result = web_search.search(query, role_title)
                return result.get('message')
        
        # 5. AI 自由對話 (Fallback)
        return self._free_chat(message, role_title)
    
    def _handle_pms_query(self, message: str, role_title: str) -> Optional[str]:
        """
        處理 PMS 資料庫查詢邏輯 (AI 意圖判斷版)
        讓 AI 判斷用戶想查什麼，而非硬編碼關鍵字
        """
        try:
            # 使用輕量 AI 判斷意圖
            intent = self._detect_query_intent(message)
            
            if not intent:
                return None
            
            intent_type = intent.get('type')
            
            # 根據意圖調用對應查詢
            if intent_type == 'today_status':
                result = internal_query.query_today_status()
            elif intent_type == 'yesterday_status':
                result = internal_query.query_yesterday_status()
            elif intent_type == 'specific_date':
                date_str = intent.get('date') or self._parse_date_from_message(message)
                if date_str:
                    result = internal_query.query_specific_date(date_str)
                else:
                    return None
            elif intent_type == 'week_forecast':
                result = internal_query.query_week_forecast(scope='week')
            elif intent_type == 'weekend_forecast':
                result = internal_query.query_week_forecast(scope='weekend')
            elif intent_type == 'month_forecast':
                result = internal_query.query_month_forecast()
            elif intent_type == 'checkin_list':
                result = internal_query.query_today_checkin_list()
            elif intent_type == 'room_status':
                result = internal_query.query_room_status()
            elif intent_type == 'same_day_bookings':
                result = internal_query.query_same_day_bookings()
            elif intent_type == 'name_search':
                name = intent.get('name', '')
                if name:
                    result = internal_query.query_booking_by_name(name)
                else:
                    return None
            else:
                return None
            
            return f"{role_title}，{result.get('message')}"
            
        except Exception as e:
            print(f"❌ PMS 查詢錯誤: {e}")
            return None
    
    def _detect_query_intent(self, message: str) -> Optional[Dict]:
        """
        使用 AI 判斷用戶的查詢意圖
        回傳: {'type': 'today_status'} 或 {'type': 'specific_date', 'date': '2025-12-25'} 等
        """
        try:
            api_key = os.getenv('GOOGLE_API_KEY')
            
            # 快速意圖分類 Prompt
            prompt = f"""你是一個意圖分類器。根據用戶訊息，判斷他想查詢什麼類型的旅館資料。

可用的查詢類型：
- today_status: 查詢今天的房況、住房率、空房數
- yesterday_status: 查詢昨天的住房狀況
- specific_date: 查詢特定日期（如 12/25、25號）的住房狀況
- week_forecast: 查詢本週（這禮拜）的入住預測
- weekend_forecast: 查詢週末（週五六日）的入住預測
- month_forecast: 查詢本月（整個月）的入住統計
- checkin_list: 查詢今天入住的客人名單
- room_status: 查詢房間清潔狀態、待打掃、停用
- same_day_bookings: 查詢今天的臨時訂單、LINE 訂單
- name_search: 查詢特定客人的訂單（需提取姓名）
- none: 不是查詢 PMS 資料的意圖

用戶訊息：「{message}」

請只回覆 JSON 格式，例如：
{{"type": "today_status"}}
{{"type": "specific_date", "date": "2025-12-25"}}
{{"type": "name_search", "name": "王小明"}}
{{"type": "none"}}"""

            # 使用新版 SDK
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=prompt
                )
                text = response.text.strip()
            except Exception:
                # Fallback 舊版 SDK
                import google.generativeai as genai_old
                genai_old.configure(api_key=api_key)
                model = genai_old.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                text = response.text.strip()
            
            # 解析 JSON
            import json
            # 移除可能的 markdown 標記
            if text.startswith('```'):
                text = text.split('\n', 1)[1].rsplit('\n', 1)[0]
            
            result = json.loads(text)
            
            if result.get('type') == 'none':
                return None
            
            return result
            
        except Exception as e:
            print(f"⚠️ 意圖判斷失敗: {e}")
            # Fallback 到簡單關鍵字匹配
            return self._fallback_keyword_detection(message)
    
    def _fallback_keyword_detection(self, message: str) -> Optional[Dict]:
        """當 AI 判斷失敗時，使用簡單關鍵字匹配作為備援"""
        if any(kw in message for kw in ['昨天', '昨日']):
            return {'type': 'yesterday_status'}
        if any(kw in message for kw in ['本月', '這個月', '這月']):
            return {'type': 'month_forecast'}
        if any(kw in message for kw in ['週末', '這週末']):
            return {'type': 'weekend_forecast'}
        if any(kw in message for kw in ['這禮拜', '本週', '這星期']):
            return {'type': 'week_forecast'}
        if any(kw in message for kw in ['房況', '住房率', '空房', '幾間房']):
            return {'type': 'today_status'}
        if any(kw in message for kw in ['入住名單', '今日入住', '誰入住']):
            return {'type': 'checkin_list'}
        if any(kw in message for kw in ['待清潔', '房間狀態', '停用']):
            return {'type': 'room_status'}
        if any(kw in message for kw in ['臨時訂單', 'LINE訂單']):
            return {'type': 'same_day_bookings'}
        
        # 特定日期檢測
        date_str = self._parse_date_from_message(message)
        if date_str:
            return {'type': 'specific_date', 'date': date_str}
        
        return None

    def _parse_date_from_message(self, message: str) -> Optional[str]:
        """
        從訊息中解析日期，回傳 YYYY-MM-DD 格式
        支援格式：12/25, 12月25日, 2025-12-25, 25號
        """
        today = datetime.now()
        
        # 格式1: YYYY-MM-DD 或 YYYY/MM/DD
        match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', message)
        if match:
            return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
        
        # 格式2: MM/DD 或 M/D
        match = re.search(r'(\d{1,2})[/](\d{1,2})', message)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{today.year}-{month:02d}-{day:02d}"
        
        # 格式3: X月X日 或 X月X號
        match = re.search(r'(\d{1,2})月(\d{1,2})[日號]?', message)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{today.year}-{month:02d}-{day:02d}"
        
        # 格式4: X號 (當月)
        match = re.search(r'(\d{1,2})[號日](?:房況|住|入住)?', message)
        if match:
            day = int(match.group(1))
            if 1 <= day <= 31:
                return f"{today.year}-{today.month:02d}-{day:02d}"
        
        return None

    def _get_standard_system_prompt(self, role_title: str, context: str = "") -> str:
        """取得標準化內部 VIP 系統指令"""
        return f"""你是龜地灣旅館的 AI 助理，正在為內部管理層人員（{role_title}）服務。

【重要身分】這是內部 VIP 對話，不受一般客服限制：
- 可以執行任何任務（翻譯、分析、寫作、建議、程式編寫等）
- 不需要詢問訂單編號或核對身分
- 回覆必須專業、有禮且高效
- 開頭務必稱呼「{role_title}」

【語言規則】
1. 語境自適應：用對方使用的語言回覆（中文問中文答、英文問英文答、印尼語問印尼語答）。
2. 只有在對方明確要求翻譯時才進行語言切換。
3. 若處理圖片，請遵循「原文辨識 + 目標語言翻譯」結構。

{context}
直接回應以下請求："""
    
    def handle_image(self, user_id: str, image_data: bytes, display_name: str = None) -> Optional[str]:
        """處理圖片 (優化版)"""
        # 只處理內部 VIP
        if not self.is_internal(user_id):
            return None
        
        if not self.vision_model:
            return "【系統錯誤】Vision 模型未初始化。"
        
        role_title = self.get_role_title(user_id)
        
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # 檢查是否有待處理任務
            pending_task = self.state_machine.get_data(user_id, 'pending_task')
            
            if pending_task:
                # 有指定任務，按任務處理
                prompt_ctx = self._build_task_prompt(pending_task, role_title)
                # 清除任務狀態
                self.state_machine.transition(user_id, 'idle')
                self.state_machine.set_data(user_id, 'pending_task', None)
            else:
                # 無指定任務，通用分析
                prompt_ctx = "請詳細分析此圖片。若有文字請完整辨識。分析完成後，請專業地詢問是否有後續處理需求（如翻譯或摘要）。"
            
            prompt = self._get_standard_system_prompt(role_title, prompt_ctx)
            response = self.vision_model.generate_content([prompt, image])
            text = response.text.strip()
            
            # 記錄對話
            if self.logger:
                self.logger.log(user_id, "User", "[傳送了一張圖片]")
                self.logger.log(user_id, "Bot (VIP Vision)", text)
            
            return text
            
        except Exception as e:
            print(f"❌ VIP 圖片處理錯誤: {e}")
            return f"{role_title}，圖片處理時發生預期外的錯誤，請確認圖片格式後再試一次。"
    
    def _detect_image_task(self, message: str) -> Optional[Dict]:
        """偵測是否為需要圖片的任務 (優化 Regex)"""
        # 翻譯任務偵測
        trans_pattern = r'(?:翻譯|translate|terjemahkan).*(?:圖|照片|image|foto|截圖)'
        if re.search(trans_pattern, message, re.IGNORECASE):
            # 簡單辨識目標語言 (可擴充)
            target_lang = "繁體中文"
            langs = {'印尼': '印尼語', '英': '英語', '日': '日語', '韓': '韓語'}
            for k, v in langs.items():
                if k in message: target_lang = v; break
                
            return {
                'type': 'translate',
                'description': f'翻譯成{target_lang}',
                'target_language': target_lang
            }
        
        # 辨識任務
        if re.search(r'(?:辨識|OCR|看懂).*(?:圖片|文字|內容)', message, re.IGNORECASE):
            return {'type': 'ocr', 'description': '辨識文字'}
        
        return None
    
    def _build_task_prompt(self, task: Dict, role_title: str) -> str:
        """建立任務特定指令"""
        task_type = task.get('type', 'general')
        
        if task_type == 'translate':
            lang = task.get('target_language', '繁體中文')
            return f"【特定任務：翻譯】請將圖中所有文字翻譯成 {lang}。請保持「原文」與「譯文」對照格式。"
        
        elif task_type == 'ocr':
            return "【特定任務：文字辨識】請完整列出圖中所有可辨識的文字，並保持原始格式。"
        
        return "請詳細分析此圖片內容。"
    
    def _free_chat(self, message: str, role_title: str) -> str:
        """AI 自由對話 (強化錯誤處理與 SDK 相容性)"""
        try:
            api_key = os.getenv('GOOGLE_API_KEY')
            system_prompt = self._get_standard_system_prompt(role_title)
            
            # 優先嘗試新版 SDK (genai client)
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                # 使用最新型號 gemini-2.0-flash-exp (或目前的 flash 穩定版)
                response = client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=f"{system_prompt}\n\n用戶要求：{message}"
                )
                if response and response.text:
                    return response.text
            except Exception:
                # Fallback 到舊版 SDK (google.generativeai)
                import google.generativeai as genai_old
                genai_old.configure(api_key=api_key)
                model = genai_old.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"{system_prompt}\n\n{message}")
                if response and response.text:
                    return response.text
                    
            return f"{role_title}，目前 AI 核心服務繁忙，請稍後再試。"
            
        except Exception as e:
            print(f"❌ VIP 對話異常: {e}")
            return f"{role_title}，對話系統發生異常，請聯絡開發團隊處理。"


# 全域實例（延遲初始化，需在 bot.py 中設定 state_machine 和 logger）
vip_service = None

def init_vip_service(state_machine, logger, vision_model=None):
    """初始化 VIP 服務"""
    global vip_service
    vip_service = VIPServiceHandler(state_machine, logger, vision_model)
    return vip_service
