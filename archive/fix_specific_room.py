#!/usr/bin/env python3
"""
修正訂單 1675334198 的房型資料
"""

import json
import re

# 讀取訂單資料
with open('chat_logs/guest_orders.json', 'r', encoding='utf-8') as f:
    orders = json.load(f)

# 修正訂單 1675334198 的房型
if '1675334198' in orders:
    order = orders['1675334198']
    room_type = order.get('room_type', '')
    
    # 從錯誤的房型中提取正確部分
    match = re.search(r'\b(Standard|Deluxe|Superior|Executive|Family|VIP|Premium|Classic|Ocean View|Sea View|Accessible)\s+(?:Single|Double|Twin|Triple|Quadruple|Family|Suite)?\s*Room', room_type, re.IGNORECASE)
    
    if match:
        correct_room_type = match.group(0).strip()
        order['room_type'] = correct_room_type
        print(f"✅ 訂單 1675334198: 修正房型 = {correct_room_type}")
        
        # 儲存
        with open('chat_logs/guest_orders.json', 'w', encoding='utf-8') as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
        print("💾 房型已儲存")
    else:
        print("⚠️ 無法提取房型")
else:
    print("❌ 找不到訂單 1675334198")
