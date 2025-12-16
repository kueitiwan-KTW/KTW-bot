#!/usr/bin/env python3
"""
修正所有現有訂單的房型，使用對應表轉換為內部代號
"""

import json
import re

# 載入房型對應表
with open('room_type_mapping.json', 'r', encoding='utf-8') as f:
    room_mapping = json.load(f)['room_type_mapping']

# 讀取訂單資料
with open('chat_logs/guest_orders.json', 'r', encoding='utf-8') as f:
    orders = json.load(f)

fixed_count = 0

for order_id, order in orders.items():
    room_type = order.get('room_type', '')
    
    if not room_type or room_type == 'null':
        continue
    
    # 清理房型名稱
    clean_room = re.sub(r'\s+\d+.*$', '', room_type)  # 移除尾部數字
    clean_room = re.sub(r'\s+No\..*$', '', clean_room)  # 移除 "No. of Rooms" 等
    clean_room = re.sub(r'\s+價格.*$', '', clean_room)  # 移除 "價格計畫" 等中文
    clean_room = re.sub(r'\s+Benefits.*$', '', clean_room, flags=re.IGNORECASE)  # 移除 "Benefits"
    clean_room = re.sub(r'\s+', ' ', clean_room).strip()
    
    # 查找對應的內部代號
    if clean_room in room_mapping:
        order['room_type'] = room_mapping[clean_room]
        print(f"✅ 訂單 {order_id}: {clean_room} → {room_mapping[clean_room]}")
        fixed_count += 1
    else:
        print(f"⚠️  訂單 {order_id}: 找不到對應 - {clean_room}")

# 儲存修復後的資料
if fixed_count > 0:
    with open('chat_logs/guest_orders.json', 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    print(f"\n🎉 已修復 {fixed_count} 筆訂單的房型資料！")
else:
    print("ℹ️ 沒有需要修復的房型資料")
