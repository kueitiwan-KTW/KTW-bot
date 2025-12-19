"""
Session 診斷工具
用於查看當前系統中所有 session 的狀態
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.conversation_state_machine import ConversationStateMachine
from handlers import OrderQueryHandler, SameDayBookingHandler
from helpers import PMSClient, GmailHelper, GoogleServices
from chat_logger import ChatLogger

def diagnose_sessions():
    """診斷所有 session 狀態"""
    
    # 初始化組件
    state_machine = ConversationStateMachine()
    pms_client = PMSClient()
    google_services = GoogleServices()
    gmail_helper = GmailHelper(google_services)
    logger = ChatLogger()
    
    # 初始化 Handlers
    order_handler = OrderQueryHandler(
        pms_client=pms_client,
        gmail_helper=gmail_helper,
        logger=logger,
        state_machine=state_machine
    )
    
    booking_handler = SameDayBookingHandler(pms_client)
    
    print("=" * 60)
    print("📊 Session 儲存位置診斷")
    print("=" * 60)
    
    # 1. ConversationStateMachine
    print("\n1️⃣  ConversationStateMachine (統一狀態機)")
    print(f"   位置: handlers/conversation_state_machine.py")
    print(f"   Session 數量: {len(state_machine.sessions)}")
    if state_machine.sessions:
        for user_id, session in state_machine.sessions.items():
            print(f"   User: {user_id}")
            print(f"     State: {session.get('state')}")
            print(f"     Pending Intent: {session.get('pending_intent')}")
    else:
        print("   (目前無 session)")
    
    # 2. OrderQueryHandler
    print("\n2️⃣  OrderQueryHandler.user_sessions")
    print(f"   位置: handlers/base_handler.py (繼承)")
    print(f"   Session 數量: {len(order_handler.user_sessions)}")
    if order_handler.user_sessions:
        for user_id, session in order_handler.user_sessions.items():
            print(f"   User: {user_id}")
            print(f"     Order ID: {session.get('order_id')}")
            print(f"     Phone: {session.get('phone')}")
    else:
        print("   (目前無 session)")
    
    # 3. SameDayBookingHandler
    print("\n3️⃣  SameDayBookingHandler.user_sessions")
    print(f"   位置: handlers/same_day_booking.py")
    print(f"   Session 數量: {len(booking_handler.user_sessions)}")
    if booking_handler.user_sessions:
        for user_id, session in booking_handler.user_sessions.items():
            print(f"   User: {user_id}")
            print(f"     State: {session.get('state')}")
            print(f"     Selected Room: {session.get('selected_room')}")
    else:
        print("   (目前無 session)")
    
    print("\n" + "=" * 60)
    print("💡 說明：")
    print("=" * 60)
    print("✅ ConversationStateMachine: 已遷移（OrderQueryHandler）")
    print("⏸️  BaseHandler.user_sessions: 仍在使用（資料儲存）")
    print("⏸️  SameDayBookingHandler: 尚未遷移，使用獨立 sessions")
    print("\n📝 建議：完成 SameDayBookingHandler 遷移後，")
    print("   所有狀態將統一存在 ConversationStateMachine")
    print("=" * 60)

if __name__ == "__main__":
    diagnose_sessions()
