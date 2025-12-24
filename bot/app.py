# Bot 主入口
# 建立日期：2025-12-24

"""
KTW Bot - 主入口

Flask 應用，處理 LINE Webhook
"""

import os
import sys
from flask import Flask, request, abort

# 確保可以導入 bot 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 從新架構導入
from L1_adapters.line.adapter import LineAdapter
from L1_adapters.base_adapter import UnifiedMessage
from L2_core.ai.intent_recognizer import IntentRecognizer
from L5_storage.database.session_manager import SessionManager
from L3_business.plugins.hotel.machines.same_day_booking import SimpleSameDayBookingMachine, BookingData
from L3_business.plugins.hotel.machines.order_query import SimpleOrderQueryMachine

# 環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
TENANT_ID = os.getenv('TENANT_ID', 'ktw_hotel')

# 初始化
app = Flask(__name__)
line_adapter = LineAdapter(LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET)
intent_recognizer = IntentRecognizer()
session_manager = SessionManager()

# LINE SDK
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 狀態機類別對照
MACHINE_CLASSES = {
    'SimpleSameDayBookingMachine': SimpleSameDayBookingMachine,
    'SimpleOrderQueryMachine': SimpleOrderQueryMachine
}


@app.route("/callback", methods=['POST'])
def callback():
    """LINE Webhook 回調"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理文字訊息"""
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    # 載入或建立 Session
    machine = session_manager.load_machine(user_id, TENANT_ID, MACHINE_CLASSES)
    
    # 處理訊息
    response = process_message(user_id, text, machine)
    
    # 回覆
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response)
    )


def process_message(user_id: str, text: str, machine=None) -> str:
    """
    處理使用者訊息
    
    流程：
    1. 如果有進行中的狀態機 → 繼續處理
    2. 如果沒有 → 識別意圖 → 建立新狀態機
    """
    
    # 如果有進行中的對話
    if machine and machine.current_state != 'idle':
        return handle_machine_input(user_id, text, machine)
    
    # 識別意圖
    intent, entities = intent_recognizer.recognize_simple(text)
    
    # 根據意圖處理
    if intent == 'same_day_booking':
        return start_same_day_booking(user_id, text, entities)
    
    elif intent == 'order_query':
        return start_order_query(user_id, text)
    
    elif intent == 'greeting':
        return "您好！我是 KTW Hotel 的 AI 客服 🏨\n\n我可以幫您：\n• 💳 當日訂房\n• 📋 查詢訂單\n• ❓ 回答問題\n\n請問有什麼需要幫忙的嗎？"
    
    elif intent == 'cancel':
        if machine:
            session_manager.clear_machine(user_id, TENANT_ID)
        return "好的，已為您取消。有需要隨時再和我說！"
    
    else:
        return f"您好！請問需要什麼服務呢？\n\n• 說「訂房」開始當日預訂\n• 說「查訂單」查詢您的預訂"


def start_same_day_booking(user_id: str, text: str, entities: Dict) -> str:
    """開始當日預訂流程"""
    machine = SimpleSameDayBookingMachine(user_id=user_id, tenant_id=TENANT_ID)
    
    # 從實體提取資訊
    room_type = entities.get('room_type', '雙人房')
    guests = entities.get('guests', 2)
    
    # 開始預訂
    response = machine.start_booking(room_type=room_type, guests=guests)
    
    # 儲存狀態
    session_manager.save_machine(user_id, TENANT_ID, machine)
    
    return response


def start_order_query(user_id: str, text: str) -> str:
    """開始訂單查詢流程"""
    machine = SimpleOrderQueryMachine(user_id=user_id, tenant_id=TENANT_ID)
    
    # TODO: 呼叫 PMS API 搜尋訂單
    # 目前先返回提示
    
    session_manager.save_machine(user_id, TENANT_ID, machine)
    
    return "請提供您的訂房大名或訂單編號，我來幫您查詢。"


def handle_machine_input(user_id: str, text: str, machine) -> str:
    """處理進行中的狀態機輸入"""
    
    # 判斷取消意圖
    if any(kw in text.lower() for kw in ['取消', '不要', '算了']):
        response = machine.cancel()
        session_manager.clear_machine(user_id, TENANT_ID)
        return response
    
    # 根據狀態機類型和當前狀態處理
    if isinstance(machine, SimpleSameDayBookingMachine):
        return handle_booking_input(user_id, text, machine)
    
    elif isinstance(machine, SimpleOrderQueryMachine):
        return handle_query_input(user_id, text, machine)
    
    return "抱歉，我不太確定您的意思。"


def handle_booking_input(user_id: str, text: str, machine: SimpleSameDayBookingMachine) -> str:
    """處理訂房流程輸入"""
    state = machine.current_state
    
    if state == 'confirming_room':
        if any(kw in text.lower() for kw in ['確認', '好', '是', '對']):
            response = machine.confirm_room()
        else:
            response = machine.cancel()
            session_manager.clear_machine(user_id, TENANT_ID)
            return response
    
    elif state == 'collecting_phone':
        response = machine.got_phone(text)
    
    elif state == 'collecting_arrival':
        response = machine.got_arrival(text)
    
    elif state == 'collecting_special':
        response = machine.complete(text if text not in ['沒有', '無', '沒'] else '')
        session_manager.clear_machine(user_id, TENANT_ID)
        return response
    
    else:
        response = "請問還有什麼需要幫忙的嗎？"
    
    # 儲存狀態
    if machine.current_state not in ['completed', 'cancelled']:
        session_manager.save_machine(user_id, TENANT_ID, machine)
    else:
        session_manager.clear_machine(user_id, TENANT_ID)
    
    return response


def handle_query_input(user_id: str, text: str, machine: SimpleOrderQueryMachine) -> str:
    """處理查詢流程輸入"""
    state = machine.current_state
    
    if state == 'idle' or state == 'searching':
        response = machine.start_query(text)
    
    elif state == 'confirming':
        if any(kw in text.lower() for kw in ['是', '對', '確認']):
            response = machine.confirm_order()
        else:
            session_manager.clear_machine(user_id, TENANT_ID)
            return "好的，請重新提供訂房資訊，我再幫您查詢。"
    
    elif state == 'collecting_phone':
        response = machine.got_phone(text)
    
    elif state == 'collecting_arrival':
        response = machine.got_arrival(text)
        session_manager.clear_machine(user_id, TENANT_ID)
        return response
    
    else:
        response = "請問還有什麼需要幫忙的嗎？"
    
    # 儲存狀態
    if machine.current_state not in ['completed', 'not_found', 'cancelled']:
        session_manager.save_machine(user_id, TENANT_ID, machine)
    else:
        session_manager.clear_machine(user_id, TENANT_ID)
    
    return response


# 需要導入
from typing import Dict


if __name__ == "__main__":
    port = int(os.getenv('PORT', 5001))
    print(f"🤖 KTW Bot 啟動中... (Port: {port})")
    app.run(host='0.0.0.0', port=port, debug=True)
