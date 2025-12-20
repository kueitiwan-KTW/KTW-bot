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
            # 取得 Dashboard 基本數據
            response = requests.get(
                f"{self.backend_url}/api/pms/dashboard",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    stats = data['data']
                    checkin_count = stats.get('todayCheckin', 0)
                    checkout_count = stats.get('todayCheckout', 0)
                    
                    # 從 rooms/status 取得更準確的房間狀態
                    try:
                        room_resp = requests.get(
                            f"{self.backend_url}/api/pms/rooms/status",
                            timeout=5
                        )
                        if room_resp.status_code == 200:
                            room_data = room_resp.json()
                            all_rooms = room_data.get('data', {}).get('rooms', [])
                            
                            # 根據 room_status 計算：
                            # - O (Occupied) = 在住
                            # - V (Vacant) = 空房 (含瑕疵房，仍可售)
                            # - R (Repair) = 維修/故障，不可售
                            occupied = len([r for r in all_rooms if r.get('room_status', {}).get('code') == 'O'])
                            vacant = len([r for r in all_rooms if r.get('room_status', {}).get('code') == 'V'])
                            repair = len([r for r in all_rooms if r.get('room_status', {}).get('code') == 'R'])
                            total = len(all_rooms)
                            
                            # 可售房 = 總房 - 維修房
                            available_total = total - repair
                            # 住房率 = 在住 / 可售房
                            rate = round((occupied / available_total * 100), 1) if available_total > 0 else 0
                        else:
                            # Fallback 舊邏輯
                            total = stats.get('totalRooms', 54)
                            occupied = stats.get('occupiedRooms', 0)
                            vacant = total - occupied
                            repair = 0
                            available_total = total
                            rate = round((occupied / total * 100), 1) if total > 0 else 0
                    except:
                        total = stats.get('totalRooms', 54)
                        occupied = stats.get('occupiedRooms', 0)
                        vacant = total - occupied
                        repair = 0
                        available_total = total
                        rate = round((occupied / total * 100), 1) if total > 0 else 0
                    
                    # 取得今日入住的房間總數
                    checkin_rooms = 0
                    try:
                        checkin_resp = requests.get(
                            f"{self.backend_url}/api/pms/today-checkin",
                            timeout=5
                        )
                        if checkin_resp.status_code == 200:
                            checkin_data = checkin_resp.json()
                            for b in checkin_data.get('data', []):
                                room_numbers = b.get('room_numbers', [])
                                checkin_rooms += len(room_numbers) if room_numbers else b.get('room_count', 1)
                    except:
                        checkin_rooms = checkin_count
                    
                    # 組合訊息
                    lines = [f"📊 今日房況"]
                    lines.append(f"━━━━━━━━━━━━━━━━━")
                    lines.append(f"• 今日入住：{checkin_count} 筆 / {checkin_rooms} 間")
                    lines.append(f"• 今日退房：{checkout_count} 筆")
                    lines.append(f"• 在住房間：{occupied} 間")
                    lines.append(f"• 可售空房：{vacant} 間")
                    if repair > 0:
                        lines.append(f"• 維修中：{repair} 間")
                    lines.append(f"• 住房率：{rate}% ({occupied}/{available_total})")
                    
                    return {
                        'success': True,
                        'today_checkin': checkin_count,
                        'today_checkin_rooms': checkin_rooms,
                        'today_checkout': checkout_count,
                        'occupied_rooms': occupied,
                        'total_rooms': total,
                        'vacant_rooms': vacant,
                        'repair_rooms': repair,
                        'occupancy_rate': rate,
                        'message': '\n'.join(lines)
                    }
            
            return {'success': False, 'message': '❌ 無法取得房況資訊'}
            
        except Exception as e:
            return {'success': False, 'message': f'❌ 查詢失敗: {str(e)}'}
    
    def query_yesterday_status(self) -> dict:
        """
        查詢昨日房況（詳細版）
        
        Returns:
            dict: 包含昨日入住數、房間數、房型分布、來源統計等資訊
        """
        try:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            weekday_name = ['一', '二', '三', '四', '五', '六', '日'][(datetime.now() - timedelta(days=1)).weekday()]
            
            booking_count = 0
            room_count = 0
            room_type_stats = {}  # 房型統計
            source_stats = {}     # 來源統計
            
            try:
                response = requests.get(
                    f"{self.pms_api_url}/api/bookings/checkin-by-date",
                    params={'date': yesterday},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    bookings = data.get('data', [])
                    booking_count = len(bookings)
                    
                    for b in bookings:
                        room_numbers = b.get('room_numbers', [])
                        rooms = len(room_numbers) if room_numbers else b.get('room_count', 1)
                        room_count += rooms
                        
                        # 統計房型 - 用實際房號查詢（昨日=已發生）
                        actual_types = self._get_actual_room_type(room_numbers)
                        for rt_name, count in actual_types.items():
                            room_type_stats[rt_name] = room_type_stats.get(rt_name, 0) + count
                        
                        # 統計來源 (從 remarks 或 ota_booking_id 判斷)
                        source = self._detect_booking_source(b)
                        source_stats[source] = source_stats.get(source, 0) + 1
                        
            except Exception as e:
                return {'success': False, 'message': f'❌ 查詢失敗: {str(e)}'}
            
            # 組合訊息
            lines = [f"📊 昨日房況 ({yesterday} 週{weekday_name})"]
            lines.append(f"━━━━━━━━━━━━━━━━━")
            lines.append(f"📈 已住統計：{booking_count} 筆 / {room_count} 間")
            
            if room_type_stats:
                lines.append(f"\n🏨 房型分布：")
                for rt, count in sorted(room_type_stats.items(), key=lambda x: -x[1]):
                    lines.append(f"• {rt}：{count} 間")
            
            if source_stats:
                lines.append(f"\n📱 訂房來源：")
                for src, count in sorted(source_stats.items(), key=lambda x: -x[1]):
                    lines.append(f"• {src}：{count} 筆")
            
            return {
                'success': True,
                'yesterday_checkin': booking_count,
                'yesterday_rooms': room_count,
                'date': yesterday,
                'room_types': room_type_stats,
                'sources': source_stats,
                'message': '\n'.join(lines)
            }
            
        except Exception as e:
            return {'success': False, 'message': f'❌ 查詢失敗: {str(e)}'}
    
    # 房號 → 房型代碼對照表（固定不變）
    ROOM_TYPE_BY_NUMBER = {
        # 2F
        '201': 'SQ', '202': 'SQ', '203': 'SD', '205': 'FM', '206': 'SD', '207': 'SD', 
        '208': 'SD', '210': 'SD', '211': 'SD', '212': 'FM', '213': 'AQ', '215': 'SQ', '216': 'SQ',
        # 3F
        '301': 'SQ', '302': 'SQ', '303': 'SQ', '305': 'FM', '306': 'SQ', '307': 'ST', 
        '308': 'ST', '309': 'ST', '310': 'ST', '311': 'ST', '312': 'FM', '313': 'AQ', '315': 'SQ', '316': 'SQ',
        # 5F
        '501': 'WQ', '502': 'WD', '503': 'WQ', '505': 'VQ', '506': 'CD', '507': 'CQ', 
        '508': 'CQ', '509': 'CD', '510': 'CQ', '511': 'CD', '512': 'VQ', '513': 'AQ', '515': 'CD', '516': 'CQ',
        # 6F
        '601': 'WD', '602': 'WD', '603': 'WD', '605': 'VD', '606': 'DD', '607': 'ED', 
        '608': 'DD', '609': 'ED', '611': 'ED', '612': 'VD', '613': 'AD', '615': 'DD', '616': 'ED',
    }
    
    def _get_room_type_name(self, code: str) -> str:
        """將房型代碼轉換為中文名稱（與 room_type_mapping.json 一致）"""
        mapping = {
            'AD': '無障礙雙人房',
            'AQ': '無障礙四人房',
            'CD': '經典雙人房',
            'CQ': '經典四人房',
            'DD': '豪華雙人房',
            'ED': '行政雙人房',
            'FM': '親子家庭房',
            'SD': '標準雙人房',
            'SQ': '標準四人房',
            'ST': '標準三人房',
            'VD': 'VIP雙人房',
            'VQ': 'VIP四人房',
            'WD': '海景雙人房',
            'WQ': '海景四人房',
            'PH': '閣樓房',
            'FD': '家庭雙人房',
            'FQ': '家庭四人房',
        }
        return mapping.get(code.strip().upper(), code or '未知房型')
    
    def _get_actual_room_type(self, room_numbers: list) -> dict:
        """
        從房號列表取得實際房型統計
        用於已發生的日期（過去/今日）
        """
        stats = {}
        for room_no in room_numbers:
            rt_code = self.ROOM_TYPE_BY_NUMBER.get(str(room_no).strip(), '')
            rt_name = self._get_room_type_name(rt_code)
            stats[rt_name] = stats.get(rt_name, 0) + 1
        return stats
    
    def _detect_booking_source(self, booking: dict) -> str:
        """偵測訂房來源"""
        ota_id = booking.get('ota_booking_id', '') or ''
        remarks = booking.get('remarks', '') or ''
        
        if 'RMAG' in ota_id or 'agoda' in remarks.lower():
            return 'Agoda'
        elif 'RMBK' in ota_id or 'booking' in remarks.lower():
            return 'Booking.com'
        elif 'RMEX' in ota_id or 'expedia' in remarks.lower():
            return 'Expedia'
        elif ota_id:
            return 'OTA'
        else:
            return '官網/電話'
    
    def query_specific_date(self, date_str: str) -> dict:
        """
        查詢特定日期房況（詳細版）
        
        Args:
            date_str: 日期字串 (YYYY-MM-DD 格式)
            
        Returns:
            dict: 包含該日入住數、房間數、房型分布、來源統計等資訊
        """
        try:
            # 解析日期以取得星期
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
            weekday_name = ['一', '二', '三', '四', '五', '六', '日'][target_date.weekday()]
            
            # 判斷是過去還是未來，決定用詞
            today = datetime.now().date()
            is_past_or_today = target_date.date() <= today
            
            if target_date.date() < today:
                time_label = "已住"
                action_label = "已住"
            elif target_date.date() == today:
                time_label = "今日"
                action_label = "入住"
            else:
                time_label = "預訂"
                action_label = "預訂"
            
            booking_count = 0
            room_count = 0
            room_type_stats = {}
            source_stats = {}
            
            try:
                response = requests.get(
                    f"{self.pms_api_url}/api/bookings/checkin-by-date",
                    params={'date': date_str},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    bookings = data.get('data', [])
                    booking_count = len(bookings)
                    
                    for b in bookings:
                        room_numbers = b.get('room_numbers', [])
                        rooms = len(room_numbers) if room_numbers else b.get('room_count', 1)
                        room_count += rooms
                        
                        # 統計房型：過去/今日用實際房型，未來用訂單房型
                        if is_past_or_today and room_numbers:
                            # 已發生：用房號查實際房型
                            actual_types = self._get_actual_room_type(room_numbers)
                            for rt_name, count in actual_types.items():
                                room_type_stats[rt_name] = room_type_stats.get(rt_name, 0) + count
                        else:
                            # 未發生：用訂單房型（計價房種）
                            for room in b.get('rooms', []):
                                rt_code = room.get('room_type_code', '').strip()
                                rt_name = self._get_room_type_name(rt_code)
                                room_type_stats[rt_name] = room_type_stats.get(rt_name, 0) + 1
                        
                        # 統計來源
                        source = self._detect_booking_source(b)
                        source_stats[source] = source_stats.get(source, 0) + 1
                        
            except Exception as e:
                return {'success': False, 'message': f'❌ 查詢失敗: {str(e)}'}
            
            # 組合訊息
            lines = [f"📊 {date_str} (週{weekday_name}) 【{time_label}】"]
            lines.append(f"━━━━━━━━━━━━━━━━━")
            lines.append(f"📈 {action_label}統計：{booking_count} 筆 / {room_count} 間")
            
            if room_type_stats:
                lines.append(f"\n🏨 房型分布：")
                for rt, count in sorted(room_type_stats.items(), key=lambda x: -x[1]):
                    lines.append(f"• {rt}：{count} 間")
            
            if source_stats:
                lines.append(f"\n📱 訂房來源：")
                for src, count in sorted(source_stats.items(), key=lambda x: -x[1]):
                    lines.append(f"• {src}：{count} 筆")
            
            return {
                'success': True,
                'checkin_count': booking_count,
                'room_count': room_count,
                'date': date_str,
                'room_types': room_type_stats,
                'sources': source_stats,
                'message': '\n'.join(lines)
            }
            
        except ValueError:
            return {'success': False, 'message': f'❌ 日期格式錯誤: {date_str}'}
        except Exception as e:
            return {'success': False, 'message': f'❌ 查詢失敗: {str(e)}'}
    
    def query_week_forecast(self, scope: str = 'week') -> dict:
        """
        查詢本週/週末入住預測
        
        Args:
            scope: 'week' (本週一到日), 'weekend' (週五六日), 'this_week' (今天到本週日)
            
        Returns:
            dict: 包含各日入住數預測
        """
        try:
            today = datetime.now()
            weekday = today.weekday()  # 0=週一, 6=週日
            
            # 計算日期範圍
            if scope == 'weekend':
                # 週五六日
                days_to_friday = (4 - weekday) % 7
                start_date = today + timedelta(days=days_to_friday)
                dates = [start_date + timedelta(days=i) for i in range(3)]
                title = "本週末 (五六日)"
            else:
                # 本週（今天到週日）
                days_to_sunday = 6 - weekday
                dates = [today + timedelta(days=i) for i in range(days_to_sunday + 1)]
                title = f"本週 ({today.strftime('%m/%d')}~{dates[-1].strftime('%m/%d')})"
            
            # 調用 PMS API 取得各日入住數
            lines = [f"📅 {title} 入住預測：\n"]
            total_bookings = 0
            total_rooms = 0
            
            for d in dates:
                date_str = d.strftime('%Y-%m-%d')
                weekday_name = ['一', '二', '三', '四', '五', '六', '日'][d.weekday()]
                
                # 計算相對天數（0=今天, 1=明天, ...）
                days_offset = (d.date() - datetime.now().date()).days
                
                # 根據日期選擇 API
                booking_count = 0
                room_count = 0
                
                try:
                    # 使用統一的 API 端點查詢任意日期
                    response = requests.get(
                        f"{self.pms_api_url}/api/bookings/checkin-by-date",
                        params={'date': date_str},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        bookings = data.get('data', [])
                        booking_count = len(bookings)
                        # 加總每筆訂單的房間數（優先用 room_numbers 長度）
                        for b in bookings:
                            room_numbers = b.get('room_numbers', [])
                            if room_numbers:
                                # 已分房：用 room_numbers 長度
                                room_count += len(room_numbers)
                            else:
                                # 未分房（未來日期）：用 rooms 陣列長度
                                rooms = b.get('rooms', [])
                                room_count += len(rooms) if rooms else 1
                except Exception as e:
                    print(f"⚠️ 查詢 {date_str} 失敗: {e}")
                
                total_bookings += booking_count
                total_rooms += room_count
                
                lines.append(f"• {d.strftime('%m/%d')} (週{weekday_name})：{booking_count} 筆 / {room_count} 間")
            
            lines.append(f"\n📊 合計：{total_bookings} 筆訂單 / {total_rooms} 間房")
            
            return {
                'success': True,
                'total_bookings': total_bookings,
                'total_rooms': total_rooms,
                'message': '\n'.join(lines)
            }
            
        except Exception as e:
            return {'success': False, 'message': f'❌ 查詢失敗: {str(e)}'}
    
    def query_month_forecast(self) -> dict:
        """
        查詢本月入住統計（完整月份：月初到月底）
        
        Returns:
            dict: 包含本月各日入住數
        """
        try:
            today = datetime.now()
            
            # 取得本月第一天與最後一天
            first_day = today.replace(day=1)
            if today.month == 12:
                last_day = datetime(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
            
            total_days = (last_day.date() - first_day.date()).days + 1
            
            # 限制查詢天數（避免太多 API 調用，最多顯示 31 天）
            if total_days > 31:
                total_days = 31
            
            title = f"{today.year}年{today.month}月 ({first_day.strftime('%m/%d')}~{last_day.strftime('%m/%d')})"
            
            lines = [f"📅 {title} 入住統計：\n"]
            lines.append("───── 已過日期 ─────")
            
            total_bookings = 0
            total_rooms = 0
            past_bookings = 0
            past_rooms = 0
            future_bookings = 0
            future_rooms = 0
            
            dates = [first_day + timedelta(days=i) for i in range(total_days)]
            
            past_lines = []
            future_lines = []
            today_line = None
            
            for d in dates:
                date_str = d.strftime('%Y-%m-%d')
                weekday_name = ['一', '二', '三', '四', '五', '六', '日'][d.weekday()]
                
                booking_count = 0
                room_count = 0
                
                try:
                    # 使用統一的 API 端點查詢任意日期
                    response = requests.get(
                        f"{self.pms_api_url}/api/bookings/checkin-by-date",
                        params={'date': date_str},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        bookings = data.get('data', [])
                        booking_count = len(bookings)
                        for b in bookings:
                            room_numbers = b.get('room_numbers', [])
                            if room_numbers:
                                room_count += len(room_numbers)
                            else:
                                rooms_list = b.get('rooms', [])
                                room_count += len(rooms_list) if rooms_list else 1
                except Exception as e:
                    print(f"⚠️ 查詢 {date_str} 失敗: {e}")
                
                total_bookings += booking_count
                total_rooms += room_count
                
                # 判斷是過去、今天還是未來
                line_text = f"• {d.strftime('%m/%d')} (週{weekday_name})：{booking_count} 筆 / {room_count} 間"
                
                if d.date() < today.date():
                    past_bookings += booking_count
                    past_rooms += room_count
                    past_lines.append(line_text)
                elif d.date() == today.date():
                    today_line = f"▶ {d.strftime('%m/%d')} (週{weekday_name})：{booking_count} 筆 / {room_count} 間 ◀ 今日"
                else:
                    future_bookings += booking_count
                    future_rooms += room_count
                    future_lines.append(line_text)
            
            # 組合輸出
            if past_lines:
                lines.extend(past_lines)
            else:
                lines.append("（無已過日期）")
                
            lines.append("\n───── 今 日 ─────")
            if today_line:
                lines.append(today_line)
            
            lines.append("\n───── 未來日期 ─────")
            if future_lines:
                lines.extend(future_lines)
            else:
                lines.append("（無未來日期）")
            
            lines.append(f"\n📊 本月合計：{total_bookings} 筆訂單 / {total_rooms} 間房")
            lines.append(f"   • 已過：{past_bookings} 筆 / {past_rooms} 間")
            lines.append(f"   • 未來：{future_bookings} 筆 / {future_rooms} 間")
            
            return {
                'success': True,
                'total_bookings': total_bookings,
                'total_rooms': total_rooms,
                'message': '\n'.join(lines)
            }
            
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
