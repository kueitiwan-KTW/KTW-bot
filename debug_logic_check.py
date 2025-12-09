from bot import HotelBot
from dotenv import load_dotenv
import os

load_dotenv()

def debug_bot_logic():
    print("--- Starting Debug Session ---")
    
    # Initialize Bot (mocking paths as they exist)
    bot = HotelBot("knowledge_base.json", "persona.md")
    
    order_id = "1675664593"
    print(f"\n--- Testing Order ID: {order_id} ---")
    
    # 1. Call logic with confirmed=False (Simulate first step)
    result = bot.check_order_status(order_id, user_confirmed=False)
    
    print("\n--- Result ---")
    print(result)
    
    if result.get('status') == 'confirmation_needed':
        print("\n[FAIL] Auto-Confirm Logic Failed. It asked for confirmation.")
    elif result.get('status') == 'blocked' or result.get('status') == 'found':
         print("\n[PASS] Auto-Confirm Logic Worked! (Or Privacy Blocked, which means it proceeded)")
    else:
         print(f"\n[?] Unexpected Status: {result.get('status')}")

if __name__ == "__main__":
    debug_bot_logic()
