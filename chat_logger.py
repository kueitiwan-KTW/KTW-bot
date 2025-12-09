import os
import datetime

import json

class ChatLogger:
    def __init__(self, log_dir="chat_logs"):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.profile_file = os.path.join(log_dir, "user_profiles.json")
        self.orders_file = os.path.join(log_dir, "guest_orders.json")
        self.profiles = self._load_profiles()
        self.orders = self._load_orders()

    def _load_profiles(self):
        if os.path.exists(self.profile_file):
            try:
                with open(self.profile_file, "r", encoding="utf-8") as f:
                    profiles = json.load(f)
                    # 向後兼容：將舊格式轉換為新格式
                    for user_id, value in profiles.items():
                        if isinstance(value, str):
                            profiles[user_id] = {
                                "display_name": value,
                                "last_interaction": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                    return profiles
            except:
                return {}
        return {}

    def save_profile(self, user_id, display_name):
        """Updates the display name for a user."""
        import datetime
        
        # 使用物件格式儲存
        self.profiles[user_id] = {
            "display_name": display_name,
            "last_interaction": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(self.profile_file, "w", encoding="utf-8") as f:
            json.dump(self.profiles, f, ensure_ascii=False, indent=2)

    def log(self, user_id, sender, message):
        """
        Logs a message to the user's log file.
        If sender is 'User', use the display name from profiles.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"{user_id}.txt"
        filepath = os.path.join(self.log_dir, filename)
        
        # 如果 sender 是 "User"，嘗試使用客人的 LINE 姓名
        if sender == "User":
            if user_id in self.profiles:
                profile = self.profiles[user_id]
                # 適配新舊格式
                if isinstance(profile, dict):
                    display_name = profile.get('display_name', 'User')
                else:
                    # 向後兼容舊格式（純字串）
                    display_name = profile
                sender = display_name
            # 如果找不到姓名，保持使用 "User"
        
        # Format: [Time] [Sender] Message
        log_entry = f"[{timestamp}] 【{sender}】\n{message}\n{'-'*30}\n"
        
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing log: {e}")

    def get_logs(self, user_id):
        """Reads the log file for a specific user."""
        filepath = os.path.join(self.log_dir, f"{user_id}.txt")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        return "尚無對話紀錄 (No logs found)."

    def list_users(self):
        """Lists all user IDs that have logs, with display names if available."""
        if not os.path.exists(self.log_dir):
            return []
        
        files = [f.replace(".txt", "") for f in os.listdir(self.log_dir) if f.endswith(".txt")]
        users_list = []
        for uid in sorted(files):
            name = self.profiles.get(uid, "Unknown")
            users_list.append({"id": uid, "name": name})
        return users_list

    # ===== 訂單管理功能 =====
    
    def _load_orders(self):
        """載入訂單資料"""
        if os.path.exists(self.orders_file):
            try:
                with open(self.orders_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_order(self, order_data):
        """將訂單儲存到訂單資料庫"""
        try:
            order_id = order_data.get('order_id', '')
            if not order_id:
                return False
            
            # 更新記憶體
            self.orders[order_id] = order_data
            
            # 寫入檔案
            with open(self.orders_file, 'w', encoding='utf-8') as f:
                json.dump(self.orders, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving order: {e}")
            return False
    
    def link_order_to_user(self, order_id, line_user_id):
        """建立訂單與 LINE 用戶的關聯"""
        if order_id not in self.orders:
            return False
        
        # 在訂單中記錄 LINE user_id
        self.orders[order_id]['line_user_id'] = line_user_id
        
        # 更新訂單
        return self.save_order(self.orders[order_id])
    
    def get_user_orders(self, line_user_id):
        """取得某個 LINE 用戶的所有訂單"""
        user_orders = []
        for order_id, order_data in self.orders.items():
            if order_data.get('line_user_id') == line_user_id:
                user_orders.append(order_data)
        return user_orders
    
    def get_order(self, order_id):
        """取得指定訂單"""
        # 重新讀取最新資料
        self.orders = self._load_orders()
        
        return self.orders.get(order_id)
    
    def update_guest_request(self, order_id, request_type, content):
        """
        更新客人需求
        request_type: 'phone', 'arrival_time', 'special_need'
        """
        if order_id not in self.orders:
            return False
        
        if 'special_requests' not in self.orders[order_id]:
            self.orders[order_id]['special_requests'] = []
        
        # 記錄需求
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        request_entry = f"[{timestamp}] {request_type}: {content}"
        self.orders[order_id]['special_requests'].append(request_entry)
        
        # 如果是電話或抵達時間，也更新主欄位
        if request_type == 'phone':
            self.orders[order_id]['phone'] = content
        elif request_type == 'arrival_time':
            self.orders[order_id]['arrival_time'] = content
        
        # 儲存
        return self.save_order(self.orders[order_id])
    
    def get_today_checkins(self):
        """取得今天入住的客人列表"""
        # 重新讀取最新資料（確保即時性）
        self.orders = self._load_orders()
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        checkins = []
        
        for order_id, order in self.orders.items():
            if order.get('check_in') == today:
                # 添加 LINE 用戶姓名（display_name）
                line_user_id = order.get('line_user_id')
                if line_user_id and line_user_id in self.profiles:
                    profile = self.profiles[line_user_id]
                    # 適配新舊格式
                    if isinstance(profile, dict):
                        order['line_display_name'] = profile.get('display_name', '未知')
                    else:
                        # 向後兼容舊格式（純字串）
                        order['line_display_name'] = profile
                else:
                    order['line_display_name'] = None
                checkins.append(order)
        
        # 按訂單編號排序
        checkins.sort(key=lambda x: x.get('order_id', ''))
        return checkins
    
    def update_admin_notes(self, order_id, notes):
        """
        更新訂單的操作人員備註
        """
        if order_id not in self.orders:
            return False
        
        self.orders[order_id]['admin_notes'] = notes
        self.orders[order_id]['updated_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 儲存
        return self.save_order(self.orders[order_id])
    
    def get_checkins_by_date(self, date_str):
        """取得指定日期入住的客人列表"""
        # 重新讀取最新資料
        self.orders = self._load_orders()
        
        checkins = []
        for order_id, order in self.orders.items():
            if order.get('check_in') == date_str:
                # 添加 LINE 用戶姓名（display_name）- 與 get_today_checkins 保持一致
                line_user_id = order.get('line_user_id')
                if line_user_id and line_user_id in self.profiles:
                    profile = self.profiles[line_user_id]
                    # 適配新舊格式
                    if isinstance(profile, dict):
                        order['line_display_name'] = profile.get('display_name', '未知')
                    else:
                        # 向後兼容舊格式（純字串）
                        order['line_display_name'] = profile
                else:
                    order['line_display_name'] = None
                checkins.append(order)
        
        # 按訂單編號排序
        checkins.sort(key=lambda x: x.get('order_id', ''))
        return checkins
