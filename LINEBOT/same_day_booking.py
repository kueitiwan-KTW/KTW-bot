"""
當日預訂對話狀態機
處理 BOT 當日預訂的多輪對話流程
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import os


class SameDayBookingHandler:
    """當日預訂處理器"""
    
    # 對話狀態常量
    STATE_IDLE = 'idle'                     # 初始狀態
    STATE_ASK_DATE = 'ask_date'             # 詢問入住日期
    STATE_SHOW_ROOMS = 'show_rooms'         # 顯示可用房型
    STATE_COLLECT_ROOM = 'collect_room'     # 收集房型選擇
    STATE_COLLECT_COUNT = 'collect_count'   # 收集房間數量
    STATE_COLLECT_BED = 'collect_bed'       # 收集床型
    STATE_COLLECT_INFO = 'collect_info'     # 收集客人資訊
    STATE_CONFIRM = 'confirm'               # 確認預訂
    STATE_COMPLETE = 'complete'             # 完成
    STATE_CANCEL_CONFIRM = 'cancel_confirm' # 確認取消訂單
    
    # 房型對照表（固定顯示的房型，使用 2/3/4 作為編號）
    AVAILABLE_ROOMS = [
        {'code': 'SD', 'name': '標準雙人房', 'price': 2800, 'beds': ['一大床', '兩小床'], 'capacity': 2},
        {'code': 'ST', 'name': '標準三人房', 'price': 3600, 'beds': ['一大床+一小床', '三小床'], 'capacity': 3},
        {'code': 'SQ', 'name': '標準四人房', 'price': 4200, 'beds': ['兩大床', '四小床'], 'capacity': 4}
    ]
    
    # 可升等的房型（依容納人數分類，VIP/家庭房不可升等）
    UPGRADABLE_ROOMS = {
        2: ['SD', 'CD', 'DD', 'ED', 'WD', 'AD'],  # 雙人房可用
        3: ['ST', 'SQ', 'CQ', 'WQ', 'AQ'],         # 三人房可用三人/四人房
        4: ['SQ', 'CQ', 'WQ', 'AQ']                # 四人房可用
    }
    
    # 無障礙房型（需特別告知）
    ACCESSIBLE_ROOMS = ['AD', 'AQ']
    
    # 完整房型對照表
    ROOM_TYPE_MAP = {
        'SD': '標準雙人房',
        'ST': '標準三人房', 
        'SQ': '標準四人房',
        'CD': '經典雙人房',
        'CQ': '經典四人房',
        'DD': '豪華雙人房',
        'ED': '行政雙人房',
        'WD': '海景雙人房',
        'WQ': '海景四人房',
        'VD': 'VIP雙人房',
        'VQ': 'VIP四人房',
        'FM': '親子家庭房',
        'AD': '無障礙雙人房',
        'AQ': '無障礙四人房'
    }
    
    def __init__(self, pms_client):
        """
        初始化處理器
        
        Args:
            pms_client: PMSClient 實例
        """
        self.pms_client = pms_client
        self.user_sessions = {}  # 用戶對話狀態 {user_id: session_data}
    
    def get_session(self, user_id: str) -> Dict[str, Any]:
        """取得或建立用戶對話 session"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'state': self.STATE_IDLE,
                'available_rooms': [],
                'selected_room': None,
                'room_count': 1,
                'bed_type': None,
                'guest_name': None,
                'phone': None,
                'arrival_time': None,
                'line_display_name': None,
                'needs_upgrade': False,
                'created_at': datetime.now().isoformat()
            }
        return self.user_sessions[user_id]
    
    def clear_session(self, user_id: str, save_interrupted: bool = False):
        """
        清除用戶 session
        
        Args:
            user_id: LINE 用戶 ID
            save_interrupted: 是否保存中斷資訊到 Dashboard
        """
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            
            # 如果已選擇房型但未完成預訂，保存為中斷狀態
            if save_interrupted and session.get('selected_room') and session.get('state') != self.STATE_IDLE:
                self._save_interrupted_booking(user_id, session)
            
            del self.user_sessions[user_id]
    
    def _save_interrupted_booking(self, user_id: str, session: Dict):
        """保存中斷的預訂資訊到 Dashboard"""
        try:
            # 建構中斷訂單資料
            today = datetime.now().strftime('%Y-%m-%d')
            room = session.get('selected_room') or {}
            
            booking_data = {
                'room_type_code': room.get('code', ''),
                'room_type_name': room.get('name', '未選定'),
                'room_count': session.get('room_count', 1),
                'bed_type': session.get('bed_type'),
                'nights': 1,
                'guest_name': session.get('guest_name', ''),
                'phone': session.get('phone', ''),
                'arrival_time': session.get('arrival_time', ''),
                'line_user_id': user_id,
                'line_display_name': session.get('line_display_name', ''),
                'status': 'interrupted'  # 中斷狀態
            }
            
            # 調用 API 保存中斷訂單
            self.pms_client.create_same_day_booking(booking_data)
            print(f"💔 已保存中斷預訂: {session.get('line_display_name', user_id)}")
            
        except Exception as e:
            print(f"⚠️ 保存中斷預訂失敗: {e}")
    
    def is_booking_intent(self, message: str) -> bool:
        """
        判斷是否為一般訂房意圖（包含當日和未來）
        
        Args:
            message: 用戶訊息
            
        Returns:
            True 如果是訂房意圖
        """
        # 排除：查詢訂單的關鍵字
        exclude_keywords = [
            '我有訂房', '我訂了', '已經訂',
            '確認訂單', '查訂單', '查詢訂單',
            '我的訂單', '訂單查詢'
        ]
        
        if any(kw in message.lower() for kw in exclude_keywords):
            return False
        
        booking_keywords = [
            '訂房', '預訂', '訂', '住', '入住', 
            '有房', '還有房', '空房', '房間',
            '想住', '要住', '可以住'
        ]
        
        message_lower = message.lower()
        return any(kw in message_lower for kw in booking_keywords)
    
    def is_same_day_intent(self, message: str) -> bool:
        """
        判斷是否為當日預訂意圖（已棄用，改用 is_booking_intent）
        
        Args:
            message: 用戶訊息
            
        Returns:
            True 如果是當日預訂意圖
        """
        keywords = [
            '今天', '今日', '當天', '當日',
            '現在', '馬上', '立刻', '等下', '等一下',
            '晚上', '今晚', '下午', '傍晚'
        ]
        booking_keywords = ['訂房', '預訂', '訂', '住', '入住', '有房', '還有房']
        
        message_lower = message.lower()
        
        # 檢查是否包含時間關鍵字 + 預訂關鍵字
        has_time = any(kw in message_lower for kw in keywords)
        has_booking = any(kw in message_lower for kw in booking_keywords)
        
        return has_time and has_booking
    
    def is_cancel_intent(self, message: str) -> bool:
        """
        判斷是否為取消訂單意圖
        
        Args:
            message: 用戶訊息
            
        Returns:
            True 如果是取消意圖
        """
        cancel_keywords = [
            '取消訂單', '取消預訂', '不住了', '不要了',
            '不來了', '取消了', '我要取消', '幫我取消',
            '想取消', '需要取消'
        ]
        return any(kw in message for kw in cancel_keywords)
    
    def _is_interrupt_intent(self, message: str) -> bool:
        """
        判斷是否要中斷當前預訂流程
        
        Args:
            message: 用戶訊息
            
        Returns:
            True 如果用戶想中斷
        """
        interrupt_keywords = [
            '不用了', '算了', '先不用', '我再想想',
            '下次', '改天', '等等', '稍後', '晚點',
            '謝謝', '謝謝你', '好的謝謝', '感謝',
            '不需要', '暫時不用', '先這樣'
        ]
        return any(kw in message for kw in interrupt_keywords)
    
    def is_within_booking_hours(self) -> bool:
        """
        檢查是否在可預訂時間內（22:00 前）
        
        Returns:
            True 如果在可預訂時間內
        """
        now = datetime.now()
        return now.hour < 22
    
    def _is_invalid_arrival_time(self, arrival_time: str) -> bool:
        """
        檢查抵達時間是否無效（超過晚上10點或隔日）
        
        Args:
            arrival_time: 客人輸入的抵達時間字串
            
        Returns:
            True 如果時間無效
        """
        import re
        
        # 檢查是否包含隔日關鍵字
        tomorrow_keywords = ['明天', '明日', '隔天', '隔日', '凌晨']
        if any(kw in arrival_time for kw in tomorrow_keywords):
            return True
        
        # 嘗試解析小時
        hour_match = re.search(r'(\d{1,2})', arrival_time)
        if not hour_match:
            return False  # 無法解析，交給人工處理
        
        hour = int(hour_match.group(1))
        
        # 判斷上午/下午/晚上
        if '晚上' in arrival_time or '晚間' in arrival_time:
            # 晚上10點以後無效
            if hour >= 10 and hour < 12:
                return True
            # 晚上11、12點無效
            if hour == 11 or hour == 12:
                return True
        elif '下午' in arrival_time or '傍晚' in arrival_time:
            # 下午轉為24小時制
            if hour < 12:
                hour += 12
            if hour >= 22:
                return True
        else:
            # 沒有前綴，根據數字判斷
            # 22點以後無效
            if hour >= 22 or hour == 0:
                return True
            # 凌晨1-6點視為隔日
            if 1 <= hour <= 6:
                return True
        
        return False
    
    def handle_message(self, user_id: str, message: str, display_name: str = None) -> Optional[str]:
        """
        處理用戶訊息
        
        Args:
            user_id: LINE 用戶 ID
            message: 用戶訊息
            display_name: LINE 顯示名稱
            
        Returns:
            回覆訊息，None 表示不是當日預訂流程
        """
        session = self.get_session(user_id)
        
        # 保存 display_name
        if display_name:
            session['line_display_name'] = display_name
        
        # 狀態機處理
        state = session['state']
        
        if state == self.STATE_IDLE:
            # 檢查是否為取消訂單意圖
            if self.is_cancel_intent(message):
                return self._start_cancel(user_id, session)
            # 檢查是否為訂房意圖（一般性）
            if self.is_booking_intent(message):
                #先檢查是否明確提到「今天」
                if self.is_same_day_intent(message):
                    # 直接進入當日預訂流程
                    return self._start_booking(user_id, session)
                else:
                    # 詢問入住日期
                    session['state'] = self.STATE_ASK_DATE
                    return """請問您想預訂哪一天入住？

您可以回覆：
• 今天 / 今日
• 明天 / 明日  
• 12/25
• 12月25日

或者告訴我具體的日期！"""
            return None  # 不是當日預訂，交給其他處理器
        
        elif state == self.STATE_ASK_DATE:
            # 處理日期輸入
            return self._handle_date_input(user_id, session, message)
        
        elif state == self.STATE_SHOW_ROOMS:
            # 檢查是否要中斷
            if self._is_interrupt_intent(message):
                self.clear_session(user_id, save_interrupted=True)
                return "好的，如有需要隨時再詢問！"
            # 等待用戶選擇房型
            return self._handle_room_selection(user_id, session, message)
        
        elif state == self.STATE_COLLECT_COUNT:
            # 檢查是否要中斷
            if self._is_interrupt_intent(message):
                self.clear_session(user_id, save_interrupted=True)
                return "好的，如有需要隨時再詢問！"
            # 收集房間數量
            return self._handle_count_collection(user_id, session, message)
        
        elif state == self.STATE_COLLECT_BED:
            # 檢查是否要中斷
            if self._is_interrupt_intent(message):
                self.clear_session(user_id, save_interrupted=True)
                return "好的，如有需要隨時再詢問！"
            # 收集床型
            return self._handle_bed_selection(user_id, session, message)
        
        elif state == self.STATE_COLLECT_INFO:
            # 檢查是否要中斷
            if self._is_interrupt_intent(message):
                self.clear_session(user_id, save_interrupted=True)
                return "好的，如有需要隨時再詢問！"
            # 收集客人資訊
            return self._handle_info_collection(user_id, session, message)
        
        elif state == self.STATE_CONFIRM:
            # 確認預訂
            return self._handle_confirmation(user_id, session, message)
        
        elif state == self.STATE_CANCEL_CONFIRM:
            # 確認取消
            return self._handle_cancel_confirmation(user_id, session, message)
        
        return None
    
    def _handle_date_input(self, user_id: str, session: Dict, message: str) -> str:
        """處理日期輸入"""
        import re
        from datetime import datetime, timedelta
        
        message_clean = message.strip()
        today = datetime.now().date()
        
        # 檢查是否為「今天」
        if any(kw in message_clean for kw in ['今天', '今日', '當日', '當天', '現在', '馬上', '立刻']):
            # 進入當日預訂流程
            return self._start_booking(user_id, session)
        
        # 檢查是否為「明天」或未來日期
        if any(kw in message_clean for kw in ['明天', '明日', '後天']):
            self.clear_session(user_id)
            return """感謝您的預訂！

由於您預訂的是未來日期，請透過我們的官網完成預訂：

🌐 線上訂房：https://ktwhotel.com/2cTrT

📋 預訂資訊：
• 入住/退房時間：15:00 入住 / 11:00 退房
• 付款方式：線上刷卡 / 現場付款
• 早餐：含自助式早餐
• 停車：提供免費停車位

如有任何問題，歡迎隨時詢問！"""
        
        # 嘗試解析具體日期（12/25, 12月25日等）
        date_patterns = [
            (r'(\d{1,2})/(\d{1,2})', '%m/%d'),           # 12/25
            (r'(\d{1,2})月(\d{1,2})日?', '%m/%d'),        # 12月25日
            (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y/%m/%d'), # 2025/12/25
        ]
        
        for pattern, date_format in date_patterns:
            match = re.search(pattern, message_clean)
            if match:
                try:
                    if len(match.groups()) == 2:
                        # 補上年份
                        month, day = map(int, match.groups())
                        year = today.year
                        # 如果日期已過，視為明年
                        check_date = datetime(year, month, day).date()
                        if check_date < today:
                            year += 1
                        target_date = datetime(year, month, day).date()
                    else:
                        # 完整日期
                        target_date = datetime.strptime(match.group(), date_format).date()
                    
                    # 判斷是否為今天
                    if target_date == today:
                        return self._start_booking(user_id, session)
                    else:
                        # 未來日期
                        self.clear_session(user_id)
                        return f"""感謝您的預訂！

您預訂的日期是：{target_date.strftime('%Y年%m月%d日')}

請透過我們的官網完成預訂：

🌐 線上訂房：https://ktwhotel.com/2cTrT

📋 預訂資訊：
• 入住/退房時間：15:00 入住 / 11:00 退房
• 付款方式：線上刷卡 / 現場付款
• 早餐：含自助式早餐
• 停車：提供免費停車位

如有任何問題，歡迎隨時詢問！"""
                except:
                    pass
        
        # 無法解析日期
        return """抱歉，我無法理解您的日期格式。

請用以下方式回覆：
• 今天 / 今日
• 明天 / 明日
• 12/25
• 12月25日

或者直接告訴我「今天想住」！"""
    
    def _start_booking(self, user_id: str, session: Dict) -> str:
        """開始預訂流程"""
        
        # 檢查時間
        if not self.is_within_booking_hours():
            self.clear_session(user_id)
            return """抱歉，當日預訂服務僅開放至晚上 10 點。

若您有住宿需求，歡迎透過官網預訂：
🌐 https://ktwhotel.com/2cTrT"""
        
        # 從 API 獲取今日房價
        result = self.pms_client.get_today_availability()
        api_prices = {}
        if result and result.get('success'):
            for room in result.get('data', {}).get('available_room_types', []):
                api_prices[room.get('room_type_code')] = room.get('price', 0)
        
        session['state'] = self.STATE_SHOW_ROOMS
        
        # 顯示房型列表（使用 API 價格）
        room_list = []
        for room in self.AVAILABLE_ROOMS:
            capacity = room['capacity']
            # 優先使用 API 價格，否則用預設價格
            price = api_prices.get(room['code'], room['price'])
            session[f"price_{room['code']}"] = price  # 保存價格到 session
            room_list.append(f"{capacity}. {room['name']} - NT${price:,}/晚（含早餐）")
        
        return f"""📋 今日可預訂房型：

{chr(10).join(room_list)}

請輸入您想預訂的房型：
• 單一房型：直接輸入編號（如：2）
• 多種房型：輸入組合（如：1間雙人1間三人）"""
    
    def _handle_room_selection(self, user_id: str, session: Dict, message: str) -> str:
        """處理房型選擇（支援單一房型和多房型）"""
        import re
        message_clean = message.strip()
        
        # 嘗試解析多房型輸入（如：1間雙人1間三人、2間雙人房1間四人房）
        multi_room_result = self._parse_multi_room_input(message_clean)
        
        if multi_room_result:
            # 多房型模式
            total_rooms = sum(item['count'] for item in multi_room_result)
            
            # 檢查總數是否超過5間
            if total_rooms >= 5:
                self.clear_session(user_id)
                return """感謝您的訂房需求！

由於您預訂的房間數較多（5間以上），為確保您的權益並享有完整服務，請透過官網預訂：

🌐 https://ktwhotel.com/2cTrT

官網預訂可線上刷卡支付訂金，確保房間保留。感謝您的理解！"""
            
            # 保存多房型選擇
            session['multi_room_orders'] = multi_room_result
            session['is_multi_room'] = True
            session['state'] = self.STATE_COLLECT_INFO
            
            # 直接進入收集資訊階段
            return self._check_multi_room_availability(user_id, session)
        
        # 單一房型模式（數字選擇 2/3/4）
        selected_room = None
        if message_clean.isdigit():
            capacity = int(message_clean)
            for room in self.AVAILABLE_ROOMS:
                if room['capacity'] == capacity:
                    selected_room = room
                    break
        
        if not selected_room:
            room_list = '\n'.join([f"{r['capacity']}. {r['name']}" for r in self.AVAILABLE_ROOMS])
            return f"""抱歉，請輸入正確的格式。

可選房型：
{room_list}

• 單一房型：直接輸入編號（如：2）
• 多種房型：輸入組合（如：1間雙人1間三人）"""
        
        # 單一房型：保存選擇
        session['selected_room'] = selected_room
        session['is_multi_room'] = False
        session['state'] = self.STATE_COLLECT_COUNT
        
        return f"""好的，您選擇了：{selected_room['name']}

請問需要幾間？（請輸入數字，1-4間）"""
    
    def _parse_multi_room_input(self, message: str) -> list:
        """
        解析多房型輸入
        支援格式：1間雙人1間三人、2間雙人房1間四人房、1雙人2三人
        
        Returns:
            list of {'room': room_dict, 'count': int} or None
        """
        import re
        
        # 房型關鍵字對照
        room_keywords = {
            '雙人': 2,
            '雙人房': 2,
            '兩人': 2,
            '2人': 2,
            '三人': 3,
            '三人房': 3,
            '3人': 3,
            '四人': 4,
            '四人房': 4,
            '4人': 4,
        }
        
        # 嘗試匹配 "數量+房型" 模式
        pattern = r'(\d+)\s*間?\s*(雙人房?|兩人|2人|三人房?|3人|四人房?|4人)'
        matches = re.findall(pattern, message)
        
        if not matches:
            return None
        
        results = []
        for count_str, room_type in matches:
            count = int(count_str)
            if count <= 0:
                continue
                
            capacity = room_keywords.get(room_type)
            if not capacity:
                continue
            
            # 找到對應的房型
            for room in self.AVAILABLE_ROOMS:
                if room['capacity'] == capacity:
                    results.append({
                        'room': room,
                        'count': count
                    })
                    break
        
        return results if results else None
    
    def _check_multi_room_availability(self, user_id: str, session: Dict) -> str:
        """檢查多房型庫存"""
        orders = session.get('multi_room_orders', [])
        
        # 查詢 API 庫存
        result = self.pms_client.get_today_availability()
        
        if not result or not result.get('success'):
            self.clear_session(user_id)
            return """抱歉，目前無法查詢房況，請稍後再試。"""
        
        available_rooms = result.get('data', {}).get('available_room_types', [])
        
        # 建構可用庫存字典
        availability = {}
        for room in available_rooms:
            code = room.get('room_type_code')
            availability[code] = room.get('available_count', 0)
        
        # 檢查每個房型的庫存
        order_lines = []
        total_price = 0
        all_available = True
        
        for order in orders:
            room = order['room']
            count = order['count']
            room_code = room['code']
            price = session.get(f"price_{room_code}", room['price'])
            
            # 取得該房型可升等的總庫存
            capacity = room['capacity']
            upgradable_codes = self.UPGRADABLE_ROOMS.get(capacity, [room_code])
            total_available = sum(availability.get(code, 0) for code in upgradable_codes)
            
            if total_available < count:
                all_available = False
            
            subtotal = price * count
            total_price += subtotal
            order_lines.append(f"• {room['name']} x {count} 間 - NT${subtotal:,}")
        
        if not all_available:
            self.clear_session(user_id)
            return f"""抱歉，目前庫存不足，無法完成您的預訂。

建議您可以查看其他日期的空房：
🌐 https://ktwhotel.com/2cTrT"""
        
        # 庫存充足，顯示確認資訊
        session['total_price'] = total_price
        
        return f"""好的，已確認您要預訂：

{chr(10).join(order_lines)}
━━━━━━━━━━━━━━━
💰 總計：NT${total_price:,}（含早餐）

請提供以下資訊以完成預訂：
1️⃣ 您的姓名
2️⃣ 聯絡電話
3️⃣ 預計抵達時間

（您可以一次提供，例如：王小明、0912345678、晚上7點）"""
    
    def _handle_count_collection(self, user_id: str, session: Dict, message: str) -> str:
        """處理房間數量收集"""
        message_clean = message.strip()
        
        # 解析數量
        import re
        count_match = re.search(r'(\d+)', message_clean)
        if not count_match:
            return "請輸入數字，例如：1"
        
        room_count = int(count_match.group(1))
        if room_count <= 0:
            return "房間數量需大於 0，請重新輸入。"
        
        # 5間以上請走官網
        if room_count >= 5:
            self.clear_session(user_id)
            return """感謝您的訂房需求！

由於您預訂的房間數較多（5間以上），為確保您的權益並享有完整服務，請透過官網預訂：

🌐 https://ktwhotel.com/2cTrT

官網預訂可線上刷卡支付訂金，確保房間保留。感謝您的理解！"""
        
        session['room_count'] = room_count
        
        # 檢查該房型是否有床型選項
        selected_room = session['selected_room']
        if len(selected_room.get('beds', [])) > 1:
            session['state'] = self.STATE_COLLECT_BED
            bed_list = '\n'.join([f"{i+1}. {bed}" for i, bed in enumerate(selected_room['beds'])])
            return f"""請選擇床型：

{bed_list}

請輸入編號（例如：1）"""
        else:
            # 只有一種床型，直接進入下一步
            if selected_room.get('beds'):
                session['bed_type'] = selected_room['beds'][0]
            session['state'] = self.STATE_COLLECT_INFO
            return self._check_availability_and_proceed(user_id, session)
    
    def _handle_bed_selection(self, user_id: str, session: Dict, message: str) -> str:
        """處理床型選擇"""
        message_clean = message.strip()
        selected_room = session['selected_room']
        beds = selected_room.get('beds', [])
        
        # 數字選擇
        if message_clean.isdigit():
            idx = int(message_clean) - 1
            if 0 <= idx < len(beds):
                session['bed_type'] = beds[idx]
                session['state'] = self.STATE_COLLECT_INFO
                return self._check_availability_and_proceed(user_id, session)
        
        bed_list = '\n'.join([f"{i+1}. {bed}" for i, bed in enumerate(beds)])
        return f"""請輸入正確的編號。

可選床型：
{bed_list}"""
    
    def _check_availability_and_proceed(self, user_id: str, session: Dict) -> str:
        """檢查庫存並繼續流程"""
        selected_room = session['selected_room']
        room_count = session['room_count']
        capacity = selected_room['capacity']
        
        # 查詢 API 庫存
        result = self.pms_client.get_today_availability()
        
        if not result or not result.get('success'):
            self.clear_session(user_id)
            return """抱歉，目前無法查詢房況，請稍後再試。"""
        
        available_rooms = result.get('data', {}).get('available_room_types', [])
        
        # 取得可升等的房型列表
        upgradable_codes = self.UPGRADABLE_ROOMS.get(capacity, [])
        
        # 計算總可用數量（館內＋網路）
        total_available = 0
        accessible_only = True  # 是否只剩無障礙房
        available_types = []    # 可用的房型列表
        
        for room in available_rooms:
            room_code = room.get('room_type_code')
            if room_code in upgradable_codes:
                count = room.get('available_count', 0)
                if count > 0:
                    total_available += count
                    available_types.append(room_code)
                    if room_code not in self.ACCESSIBLE_ROOMS:
                        accessible_only = False
        
        # 檢查庫存
        if total_available >= room_count:
            # 庫存充足
            bed_info = f" - {session.get('bed_type')}" if session.get('bed_type') else ""
            
            # 如果只剩無障礙房，需要告知
            accessible_notice = ""
            if accessible_only and any(code in self.ACCESSIBLE_ROOMS for code in available_types):
                accessible_notice = "\n\n⚠️ 目前僅剩無障礙房型，此房型只有淋浴間為無障礙設計，其餘房內設施與一般房間相同。"
            
            return f"""好的，已確認：
🏨 {selected_room['name']}{bed_info} x {room_count} 間{accessible_notice}

請提供以下資訊以完成預訂：
1️⃣ 您的姓名
2️⃣ 聯絡電話
3️⃣ 預計抵達時間

（您可以一次提供，例如：王小明、0912345678、晚上7點）"""
        else:
            # 庫存不足
            self.clear_session(user_id)
            return f"""抱歉，目前{selected_room['name']}已無空房。

建議您可以查看其他日期的空房：
🌐 https://ktwhotel.com/2cTrT"""
    
    def _handle_info_collection(self, user_id: str, session: Dict, message: str) -> str:
        """收集客人資訊"""
        import re
        
        # 嘗試解析姓名、電話、時間
        # 電話格式：09xxxxxxxx
        phone_match = re.search(r'(09\d{8})', message.replace('-', '').replace(' ', ''))
        if phone_match:
            session['phone'] = phone_match.group(1)
        
        # 時間格式：各種表達方式
        time_patterns = [
            r'(下午\d+點)', r'(晚上\d+點)', r'(傍晚\d+點)', r'(上午\d+點)',
            r'(\d{1,2}[點:：]\d{0,2})', r'(\d{1,2}點)',
            r'(大約\S+)', r'(約\S+點)',
        ]
        for pattern in time_patterns:
            time_match = re.search(pattern, message)
            if time_match:
                session['arrival_time'] = time_match.group(1)
                break
        
        # 姓名：排除電話和時間後的中文/英文
        remaining = message
        if phone_match:
            remaining = remaining.replace(phone_match.group(1), '')
        if session.get('arrival_time'):
            remaining = remaining.replace(session['arrival_time'], '')
        
        # 嘗試提取姓名
        name_match = re.search(r'([一-龥A-Za-z]{2,10})', remaining.replace(',', '').replace('，', '').strip())
        if name_match and not session.get('guest_name'):
            potential_name = name_match.group(1)
            # 排除常見非姓名詞
            exclude_words = ['晚上', '下午', '傍晚', '上午', '點', '間', '房']
            if not any(word in potential_name for word in exclude_words):
                session['guest_name'] = potential_name
        
        # 檢查是否收集完整
        missing = []
        if not session.get('guest_name'):
            missing.append('姓名')
        if not session.get('phone'):
            missing.append('聯絡電話')
        if not session.get('arrival_time'):
            missing.append('預計抵達時間')
        
        if missing:
            return f"請再提供：{'、'.join(missing)}"
        
        # 檢查抵達時間是否有效（不接受晚上10點後或隔日）
        arrival_time = session.get('arrival_time', '')
        if self._is_invalid_arrival_time(arrival_time):
            self.clear_session(user_id)
            return """抱歉，當日預訂僅接受今日晚上 10 點前抵達的訂單。

如需隔日入住，請透過官網預訂：
🌐 https://ktwhotel.com/2cTrT"""
        
        # 資訊完整，進入確認階段
        session['state'] = self.STATE_CONFIRM
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 根據是否為多房型生成不同的確認訊息
        if session.get('is_multi_room'):
            # 多房型模式
            orders = session.get('multi_room_orders', [])
            room_lines = []
            for order in orders:
                room = order['room']
                count = order['count']
                room_lines.append(f"• {room['name']} x {count} 間")
            
            total_price = session.get('total_price', 0)
            
            return f"""📋 請確認預訂資訊：

🏨 房型：
{chr(10).join(room_lines)}
💰 總計：NT${total_price:,}（含早餐）
📅 入住日期：{today}（今日）
👤 姓名：{session['guest_name']}
📞 電話：{session['phone']}
🕐 抵達時間：{session['arrival_time']}
💬 LINE 姓名：{session.get('line_display_name', '未提供')}

請輸入：
1️⃣ 確認預訂
2️⃣ 取消預訂"""
        else:
            # 單一房型模式
            room = session['selected_room']
            room_name = room['name']
            bed_info = f" - {session.get('bed_type')}" if session.get('bed_type') else ""
            
            return f"""📋 請確認預訂資訊：

🏨 房型：{room_name}{bed_info} x {session['room_count']} 間
📅 入住日期：{today}（今日）
👤 姓名：{session['guest_name']}
📞 電話：{session['phone']}
🕐 抵達時間：{session['arrival_time']}
💬 LINE 姓名：{session.get('line_display_name', '未提供')}

請輸入：
1️⃣ 確認預訂
2️⃣ 取消預訂"""
    
    def _handle_confirmation(self, user_id: str, session: Dict, message: str) -> str:
        """處理預訂確認"""
        message_clean = message.strip()
        
        # 數字選擇
        if message_clean == '2':
            self.clear_session(user_id)
            return "好的，已取消預訂。如有需要歡迎再次詢問！"
        
        if message_clean == '1':
            return self._create_booking(user_id, session)
        
        return """請輸入：
1️⃣ 確認預訂
2️⃣ 取消預訂"""
    
    def _create_booking(self, user_id: str, session: Dict) -> str:
        """建立預訂（支援單一房型和多房型）"""
        
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 判斷是多房型還是單一房型
        if session.get('is_multi_room'):
            return self._create_multi_room_booking(user_id, session, today, tomorrow)
        else:
            return self._create_single_room_booking(user_id, session, today, tomorrow)
    
    def _create_single_room_booking(self, user_id: str, session: Dict, today: str, tomorrow: str) -> str:
        """建立單一房型預訂"""
        room = session['selected_room']
        
        booking_data = {
            'room_type_code': room.get('code'),
            'room_type_name': room.get('name'),
            'room_count': session['room_count'],
            'bed_type': session.get('bed_type'),
            'nights': 1,
            'guest_name': session['guest_name'],
            'phone': session['phone'],
            'arrival_time': session['arrival_time'],
            'line_user_id': user_id,
            'line_display_name': session.get('line_display_name'),
            'needs_upgrade': session.get('needs_upgrade', False)
        }
        
        result = self.pms_client.create_same_day_booking(booking_data)
        
        if not result or not result.get('success'):
            error_msg = result.get('error', {}).get('message', '系統錯誤') if result else '連線失敗'
            self.clear_session(user_id)
            return f"""抱歉，預訂失敗：{error_msg}

請稍後再試。"""
        
        # 成功
        order_id = result.get('data', {}).get('temp_order_id', '未知')
        room_name = room.get('name')
        bed_info = f" - {session.get('bed_type')}" if session.get('bed_type') else ""
        
        # 寫入 guest_orders.json
        self._save_to_guest_orders(
            order_id=order_id,
            user_id=user_id,
            session=session,
            room=room,
            check_in=today,
            check_out=tomorrow
        )
        
        self.clear_session(user_id)
        
        return f"""✅ 預訂成功！

📋 預訂資訊：
━━━━━━━━━━━━━━━
🏨 房型：{room_name}{bed_info} x {session['room_count']} 間  
📅 入住日期：{today}
👤 姓名：{session['guest_name']}
📞 電話：{session['phone']}
🕐 抵達時間：{session['arrival_time']}
💬 LINE 姓名：{session.get('line_display_name', '未提供')}
━━━━━━━━━━━━━━━

⚠️ 當日預訂注意事項：
• 由於旅棧採預約訂金制，當日或即時預訂無收取訂金，館方保留臨時取消之權利
• 如需確保必能有房間，可採官網預訂線上刷卡支付訂金：https://ktwhotel.com/2cTrT
• 請務必於預定時間抵達飯店櫃檯辦理入住
• 如有更變需取消預訂，務必 LINE 告之

期待您的光臨！🌊"""
    
    def _create_multi_room_booking(self, user_id: str, session: Dict, today: str, tomorrow: str) -> str:
        """建立多房型預訂"""
        orders = session.get('multi_room_orders', [])
        created_orders = []
        room_lines = []
        
        for order in orders:
            room = order['room']
            count = order['count']
            
            booking_data = {
                'room_type_code': room.get('code'),
                'room_type_name': room.get('name'),
                'room_count': count,
                'nights': 1,
                'guest_name': session['guest_name'],
                'phone': session['phone'],
                'arrival_time': session['arrival_time'],
                'line_user_id': user_id,
                'line_display_name': session.get('line_display_name')
            }
            
            result = self.pms_client.create_same_day_booking(booking_data)
            
            if result and result.get('success'):
                order_id = result.get('data', {}).get('temp_order_id', '未知')
                created_orders.append(order_id)
                
                # 寫入 guest_orders.json
                self._save_to_guest_orders(
                    order_id=order_id,
                    user_id=user_id,
                    session=session,
                    room=room,
                    check_in=today,
                    check_out=tomorrow
                )
            
            room_lines.append(f"• {room['name']} x {count} 間")
        
        if not created_orders:
            self.clear_session(user_id)
            return """抱歉，預訂失敗，請稍後再試。"""
        
        self.clear_session(user_id)
        
        total_price = session.get('total_price', 0)
        
        return f"""✅ 預訂成功！

📋 預訂資訊：
━━━━━━━━━━━━━━━
🏨 房型：
{chr(10).join(room_lines)}
💰 總計：NT${total_price:,}（含早餐）
📅 入住日期：{today}
👤 姓名：{session['guest_name']}
📞 電話：{session['phone']}
🕐 抵達時間：{session['arrival_time']}
💬 LINE 姓名：{session.get('line_display_name', '未提供')}
━━━━━━━━━━━━━━━

⚠️ 當日預訂注意事項：
• 由於旅棧採預約訂金制，當日或即時預訂無收取訂金，館方保留臨時取消之權利
• 如需確保必能有房間，可採官網預訂線上刷卡支付訂金：https://ktwhotel.com/2cTrT
• 請務必於預定時間抵達飯店櫃檯辦理入住
• 如有更變需取消預訂，務必 LINE 告之

期待您的光臨！🌊"""
    
    def _save_to_guest_orders(self, order_id: str, user_id: str, session: Dict, 
                               room: Dict, check_in: str, check_out: str):
        """將當日預訂寫入 guest_orders.json"""
        try:
            # 檔案路徑
            orders_file = os.path.join(os.path.dirname(__file__), 'chat_logs', 'guest_orders.json')
            
            # 讀取現有資料
            orders = {}
            if os.path.exists(orders_file):
                with open(orders_file, 'r', encoding='utf-8') as f:
                    orders = json.load(f)
            
            # 建立訂單記錄
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            room_code = room.get('code', 'SD')
            room_name = room.get('name', '標準雙人房')
            bed_type = session.get('bed_type', '')
            
            order_data = {
                'order_id': order_id,
                'line_user_id': user_id,
                'line_display_name': session.get('line_display_name', ''),
                'check_in': check_in,
                'check_out': check_out,
                'room_type': f"{room_code}-{room_name}",
                'room_count': session.get('room_count', 1),
                'bed_type': bed_type,
                'guest_name': session.get('guest_name', ''),
                'phone': session.get('phone', ''),
                'arrival_time': session.get('arrival_time', ''),
                'booking_source': 'LINE當日預訂',
                'breakfast': True,  # 當日預訂含早餐
                'created_at': now,
                'updated_at': now,
                'special_requests': [
                    f"[{now}] 當日預訂",
                    f"[{now}] 床型: {bed_type}" if bed_type else None,
                    f"[{now}] arrival_time: {session.get('arrival_time', '')}"
                ]
            }
            
            # 清除 None 值
            order_data['special_requests'] = [r for r in order_data['special_requests'] if r]
            
            # 寫入
            orders[order_id] = order_data
            
            with open(orders_file, 'w', encoding='utf-8') as f:
                json.dump(orders, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 已寫入 guest_orders.json: {order_id}")
            
        except Exception as e:
            print(f"⚠️ 寫入 guest_orders.json 失敗: {e}")
    
    def is_in_booking_flow(self, user_id: str) -> bool:
        """
        檢查用戶是否在預訂流程中
        
        Args:
            user_id: LINE 用戶 ID
            
        Returns:
            True 如果用戶正在進行當日預訂
        """
        session = self.user_sessions.get(user_id)
        if not session:
            return False
        return session.get('state', self.STATE_IDLE) != self.STATE_IDLE
    
    def _start_cancel(self, user_id: str, session: Dict) -> str:
        """開始取消流程"""
        
        # 查詢該用戶的 pending 訂單
        result = self.pms_client.get_same_day_bookings()
        
        if not result or not result.get('success'):
            self.clear_session(user_id)
            return """抱歉，目前無法查詢訂單，請稍後再試。"""
        
        bookings = result.get('data', [])
        
        # 找出該用戶的 pending 或 interrupted 訂單
        user_bookings = [b for b in bookings 
                        if b.get('line_user_id') == user_id 
                        and b.get('status') in ['pending', 'interrupted']]
        
        if not user_bookings:
            self.clear_session(user_id)
            return """您目前沒有待處理的當日訂單。

如有其他問題，請隨時詢問！"""
        
        # 取第一筆（通常只會有一筆）
        booking = user_bookings[0]
        session['cancel_booking'] = booking
        session['state'] = self.STATE_CANCEL_CONFIRM
        
        room_name = booking.get('room_type_name', booking.get('room_type_code', '未知'))
        bed_info = f" - {booking.get('bed_type')}" if booking.get('bed_type') else ""
        status_text = "待入住" if booking.get('status') == 'pending' else "預約中斷"
        
        return f"""📋 您有一筆{status_text}的當日訂單：

🏨 房型：{room_name}{bed_info} x {booking.get('room_count', 1)} 間
👤 姓名：{booking.get('guest_name', '-')}
🕐 預計抵達：{booking.get('arrival_time', '-')}

請問確定要取消嗎？
1️⃣ 確認取消
2️⃣ 保留訂單"""
    
    def _handle_cancel_confirmation(self, user_id: str, session: Dict, message: str) -> str:
        """處理取消確認"""
        message_clean = message.strip()
        
        # 保留訂單
        if message_clean == '2':
            self.clear_session(user_id)
            return "好的，已為您保留訂單。期待您的光臨！🌊"
        
        # 確認取消
        if message_clean == '1':
            return self._execute_cancel(user_id, session)
        
        return """請輸入：
1️⃣ 確認取消
2️⃣ 保留訂單"""
    
    def _execute_cancel(self, user_id: str, session: Dict) -> str:
        """執行取消訂單"""
        booking = session.get('cancel_booking')
        
        if not booking:
            self.clear_session(user_id)
            return "訂單資料遺失，請重新操作。"
        
        order_id = booking.get('temp_order_id')
        
        # 調用取消 API
        result = self.pms_client.cancel_same_day_booking(order_id)
        
        if not result or not result.get('success'):
            error_msg = result.get('error', {}).get('message', '系統錯誤') if result else '連線失敗'
            self.clear_session(user_id)
            return f"""抱歉，取消失敗：{error_msg}

請稍後再試。"""
        
        self.clear_session(user_id)
        
        room_name = booking.get('room_type_name', booking.get('room_type_code'))
        
        return f"""✅ 已為您取消訂單！

📋 已取消的訂單資訊：
━━━━━━━━━━━━━━━
🏨 房型：{room_name}
👤 姓名：{booking.get('guest_name', '-')}
━━━━━━━━━━━━━━━

如有需要隨時歡迎再次預訂！"""
