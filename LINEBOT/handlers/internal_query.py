"""
內部 VIP 專用查詢模組
提供 PMS 資料庫查詢功能，僅限內部 VIP 使用
"""

import requests
import os
from datetime import datetime, timedelta

class InternalQueryHandler:
    """內部 VIP 專用查詢器"""
    
    def __init__(self):
        self.backend_url = os.getenv('KTW_BACKEND_URL', 'http://localhost:3000')
        self.pms_api_url = os.getenv('PMS_API_URL', 'http://192.168.8.3:3000')
    
    def query_today_status(self) -> dict:
        """
        查詢今日房況
        
        Returns:
            dict: 包含入住數、退房數、住房率等資訊
        """
        try:
            response = requests.get(
                f"{self.backend_url}/api/pms/dashboard",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    stats = data['data']
                    total = stats.get('totalRooms', 0)
                    occupied = stats.get('occupiedRooms', 0)
                    rate = round((occupied / total * 100), 1) if total > 0 else 0
                    
                    return {
                        'success': True,
                        'today_checkin': stats.get('todayCheckin', 0),
                        'today_checkout': stats.get('todayCheckout', 0),
                        'occupied_rooms': occupied,
                        'total_rooms': total,
                        'vacant_rooms': total - occupied,
                        'occupancy_rate': rate,
                        'message': f"📊 今日房況：\n"
                                   f"• 入住：{stats.get('todayCheckin', 0)} 組\n"
                                   f"• 退房：{stats.get('todayCheckout', 0)} 組\n"
                                   f"• 住房率：{rate}% ({occupied}/{total})\n"
                                   f"• 空房：{total - occupied} 間"
                    }
            
            return {'success': False, 'message': '❌ 無法取得房況資訊'}
            
        except Exception as e:
            return {'success': False, 'message': f'❌ 查詢失敗: {str(e)}'}
    
    def query_today_checkin_list(self) -> dict:
        """
        查詢今日入住名單
        
        Returns:
            dict: 包含今日入住客人列表
        """
        try:
            response = requests.get(
                f"{self.backend_url}/api/pms/today-checkin",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    bookings = data['data']
                    
                    if not bookings:
                        return {'success': True, 'count': 0, 'message': '📋 今日沒有入住訂單'}
                    
                    lines = [f"📋 今日入住 ({len(bookings)} 組)：\n"]
                    for i, b in enumerate(bookings[:10], 1):  # 最多顯示 10 筆
                        name = b.get('guest_name', '未知')
                        room = b.get('room_type_name', '未知')
                        source = b.get('booking_source', '')
                        lines.append(f"{i}. {name} - {room} ({source})")
                    
                    if len(bookings) > 10:
                        lines.append(f"... 還有 {len(bookings) - 10} 組")
                    
                    return {
                        'success': True,
                        'count': len(bookings),
                        'bookings': bookings,
                        'message': '\n'.join(lines)
                    }
            
            return {'success': False, 'message': '❌ 無法取得入住名單'}
            
        except Exception as e:
            return {'success': False, 'message': f'❌ 查詢失敗: {str(e)}'}
    
    def query_booking_by_name(self, name: str) -> dict:
        """
        依姓名查詢訂單
        
        Args:
            name: 客人姓名
            
        Returns:
            dict: 查詢結果
        """
        try:
            # 先從今日入住名單找
            response = requests.get(
                f"{self.backend_url}/api/pms/today-checkin",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                bookings = data.get('data', [])
                
                # 模糊匹配姓名
                matches = []
                for b in bookings:
                    guest_name = b.get('guest_name', '')
                    if name.lower() in guest_name.lower() or guest_name.lower() in name.lower():
                        matches.append(b)
                
                if matches:
                    lines = [f"🔍 找到 {len(matches)} 筆符合 '{name}' 的訂單：\n"]
                    for b in matches:
                        lines.append(
                            f"• {b.get('guest_name')} - {b.get('room_type_name')}\n"
                            f"  訂單號：{b.get('booking_id')}\n"
                            f"  電話：{b.get('contact_phone', '無')}\n"
                            f"  入住：{b.get('check_in_date')} ~ {b.get('check_out_date')}"
                        )
                    
                    return {'success': True, 'count': len(matches), 'bookings': matches, 'message': '\n'.join(lines)}
                else:
                    return {'success': True, 'count': 0, 'message': f'🔍 今日入住名單中找不到 "{name}"'}
            
            return {'success': False, 'message': '❌ 查詢失敗'}
            
        except Exception as e:
            return {'success': False, 'message': f'❌ 查詢失敗: {str(e)}'}
    
    def query_room_status(self) -> dict:
        """
        查詢房間狀態（清潔/停用）
        
        Returns:
            dict: 房間狀態資訊
        """
        try:
            response = requests.get(
                f"{self.backend_url}/api/pms/rooms/status",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    stats = data['data'].get('stats', {})
                    
                    return {
                        'success': True,
                        'stats': stats,
                        'message': f"🏨 房間狀態：\n"
                                   f"• 總房數：{stats.get('total', 0)}\n"
                                   f"• 已入住：{stats.get('occupied', 0)}\n"
                                   f"• 空房：{stats.get('vacant', 0)}\n"
                                   f"• 待清潔：{stats.get('dirty', 0)}\n"
                                   f"• 停用：{stats.get('out_of_order', 0)}"
                    }
            
            return {'success': False, 'message': '❌ 無法取得房間狀態'}
            
        except Exception as e:
            return {'success': False, 'message': f'❌ 查詢失敗: {str(e)}'}
    
    def query_same_day_bookings(self) -> dict:
        """
        查詢 LINE Bot 當日預訂（臨時訂單）
        
        Returns:
            dict: 臨時訂單列表
        """
        try:
            response = requests.get(
                f"{self.backend_url}/api/pms/same-day-bookings",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    bookings = data['data'].get('bookings', [])
                    
                    if not bookings:
                        return {'success': True, 'count': 0, 'message': '📱 今日沒有 LINE 臨時預訂'}
                    
                    # 依狀態分類
                    pending = [b for b in bookings if b.get('status') == 'pending']
                    checked = [b for b in bookings if b.get('status') == 'checked_in']
                    
                    lines = [f"📱 LINE 當日預訂 ({len(bookings)} 筆)：\n"]
                    
                    if pending:
                        lines.append(f"🟡 待入住 ({len(pending)}):")
                        for b in pending[:5]:
                            lines.append(f"  • {b.get('guest_name')} - {b.get('room_description')}")
                    
                    if checked:
                        lines.append(f"🟢 已KEY ({len(checked)}):")
                        for b in checked[:5]:
                            lines.append(f"  • {b.get('guest_name')}")
                    
                    return {
                        'success': True,
                        'count': len(bookings),
                        'pending': len(pending),
                        'checked_in': len(checked),
                        'message': '\n'.join(lines)
                    }
            
            return {'success': False, 'message': '❌ 無法取得臨時訂單'}
            
        except Exception as e:
            return {'success': False, 'message': f'❌ 查詢失敗: {str(e)}'}


# 建立全域實例
internal_query = InternalQueryHandler()


# ============================================
# Function Calling 定義 (供 bot.py 使用)
# ============================================

INTERNAL_VIP_FUNCTIONS = [
    {
        "name": "query_today_status",
        "description": "查詢今日房況摘要，包含入住數、退房數、住房率、空房數。僅限內部 VIP 使用。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "query_today_checkin_list",
        "description": "查詢今日入住客人名單，包含姓名、房型、訂房來源。僅限內部 VIP 使用。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "query_booking_by_name",
        "description": "依客人姓名查詢訂單資訊。僅限內部 VIP 使用。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "要查詢的客人姓名"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "query_room_status",
        "description": "查詢房間清潔狀態，包含已入住、空房、待清潔、停用等統計。僅限內部 VIP 使用。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "query_same_day_bookings",
        "description": "查詢 LINE Bot 當日預訂（臨時訂單）列表，包含待入住和已 KEY 狀態。僅限內部 VIP 使用。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]


def execute_internal_query(function_name: str, arguments: dict) -> str:
    """
    執行內部查詢 Function
    
    Args:
        function_name: 函數名稱
        arguments: 參數
        
    Returns:
        str: 查詢結果訊息
    """
    handler = internal_query
    
    if function_name == "query_today_status":
        result = handler.query_today_status()
    elif function_name == "query_today_checkin_list":
        result = handler.query_today_checkin_list()
    elif function_name == "query_booking_by_name":
        result = handler.query_booking_by_name(arguments.get('name', ''))
    elif function_name == "query_room_status":
        result = handler.query_room_status()
    elif function_name == "query_same_day_bookings":
        result = handler.query_same_day_bookings()
    else:
        return f"❌ 未知的查詢功能: {function_name}"
    
    return result.get('message', '查詢完成')
