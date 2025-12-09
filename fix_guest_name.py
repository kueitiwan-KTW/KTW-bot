#!/usr/bin/env python3
"""
修正現有訂單的客人姓名
移除 "Customer Last Name" 等多餘文字
"""

import json
import re

# 讀取訂單資料
with open('chat_logs/guest_orders.json', 'r', encoding='utf-8') as f:
    orders = json.load(f)

fixed_count = 0

for order_id, order in orders.items():
    guest_name = order.get('guest_name', '')
    
    # 如果姓名包含 "Customer Last Name" 等錯誤內容
    if guest_name and ('Customer' in guest_name or 'Last Name' in guest_name):
        # 只保留第一個有效的名字部分
        parts = guest_name.split()
        clean_parts = [p for p in parts if p not in ['Customer', 'Last', 'Name', 'First']]
        
        if clean_parts:
            correct_name = ' '.join(clean_parts[:2])  # 最多保留兩個詞（名 + 姓）
            order['guest_name'] = correct_name
            print(f"✅ 訂單 {order_id}: 修正姓名 = {correct_name}")
            fixed_count += 1

# 儲存修復後的資料
if fixed_count > 0:
    with open('chat_logs/guest_orders.json', 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    print(f"\n🎉 已修復 {fixed_count} 筆訂單的姓名資料！")
else:
    print("ℹ️ 沒有需要修復的姓名資料")
