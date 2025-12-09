#!/usr/bin/env python3
"""
修復現有訂單資料的腳本
- 從 special_requests 提取 phone 和 arrival_time 到主欄位
- 確保資料正確顯示在管理後台
"""

import json
import re

# 讀取訂單資料
with open('chat_logs/guest_orders.json', 'r', encoding='utf-8') as f:
    orders = json.load(f)

fixed_count = 0

for order_id, order in orders.items():
    modified = False
    
    # 檢查 special_requests
    if 'special_requests' in order and order['special_requests']:
        # 提取最新的 phone
        phone_vals = [req.split(': ', 1)[1] for req in order['special_requests'] if req.startswith('[') and 'phone:' in req]
        if phone_vals and not order.get('phone'):
            order['phone'] = phone_vals[-1]  # 使用最新的
            modified = True
            print(f"✅ 訂單 {order_id}: 設置電話 = {phone_vals[-1]}")
        
        # 提取最新的 arrival_time  
        arrival_vals = [req.split(': ', 1)[1] for req in order['special_requests'] if req.startswith('[') and 'arrival_time:' in req]
        if arrival_vals and not order.get('arrival_time'):
            order['arrival_time'] = arrival_vals[-1]  # 使用最新的
            modified = True
            print(f"✅ 訂單 {order_id}: 設置抵達時間 = {arrival_vals[-1]}")
    
    if modified:
        fixed_count += 1

# 儲存修復後的資料
if fixed_count > 0:
    with open('chat_logs/guest_orders.json', 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    print(f"\n🎉 已修復 {fixed_count} 筆訂單資料！")
else:
    print("ℹ️ 沒有需要修復的資料")
