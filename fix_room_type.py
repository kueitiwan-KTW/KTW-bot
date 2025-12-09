#!/usr/bin/env python3
"""
修正現有訂單的房型資料
從錯誤的提取結果中清理出正確的房型
"""

import json
import re

# 讀取訂單資料
with open('chat_logs/guest_orders.json', 'r', encoding='utf-8') as f:
    orders = json.load(f)

fixed_count = 0

for order_id, order in orders.items():
    room_type = order.get('room_type')
    
    # 如果房型包含 "of Rooms" 等錯誤內容
    if room_type and ('of Rooms' in room_type or '房間數' in room_type):
        # 從錯誤字串中提取正確的房型
        match = re.search(r'\b(Standard|Deluxe|Superior|Executive|Family|VIP|Premium|Classic|Ocean View|Sea View|Accessible)\s+(?:Single|Double|Twin|Triple|Quadruple|Family|Suite)?\s*Room[^\n,]*(?:Non-Smoking|Smoking)?', room_type, re.IGNORECASE)
        
        if match:
            correct_room_type = match.group(0).strip()
            order['room_type'] = correct_room_type
            print(f"✅ 訂單 {order_id}: 修正房型 = {correct_room_type}")
            fixed_count += 1
        else:
            # 如果無法提取，設為 None
            order['room_type'] = None
            print(f"⚠️  訂單 {order_id}: 無法提取房型，設為 None")
            fixed_count += 1

# 儲存修復後的資料
if fixed_count > 0:
    with open('chat_logs/guest_orders.json', 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    print(f"\n🎉 已修復 {fixed_count} 筆訂單的房型資料！")
else:
    print("ℹ️ 沒有需要修復的房型資料")
