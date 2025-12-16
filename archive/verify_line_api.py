import os
import sys
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError

# Load environment variables
load_dotenv()

def verify_line_api():
    token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    secret = os.getenv('LINE_CHANNEL_SECRET')

    print(f"Checking credentials...")
    if not token or token == 'YOUR_ACCESS_TOKEN':
        print("❌ Error: LINE_CHANNEL_ACCESS_TOKEN is not set in .env")
        return
    if not secret or secret == 'YOUR_CHANNEL_SECRET':
        print("❌ Error: LINE_CHANNEL_SECRET is not set in .env")
        return

    try:
        api = LineBotApi(token)
        # Try to get bot info to verify token
        bot_info = api.get_bot_info()
        print("✅ LINE API Connection Successful!")
        print(f"Bot Name: {bot_info.display_name}")
        print(f"Bot User ID: {bot_info.user_id}")
        print(f"Mark as Basic ID: {bot_info.basic_id}")
    except LineBotApiError as e:
        print(f"❌ LINE API Error: {e.status_code} {e.message}")
        print("Please check your LINE_CHANNEL_ACCESS_TOKEN.")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    verify_line_api()
