import os
import sys
import json
import hmac
import hashlib
import base64
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_signature(channel_secret, body):
    hash = hmac.new(
        channel_secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash).decode('utf-8')

def simulate_webhook():
    secret = os.getenv('LINE_CHANNEL_SECRET')
    if not secret or secret == 'YOUR_CHANNEL_SECRET':
        print("❌ Error: LINE_CHANNEL_SECRET is not set in .env")
        return

    # Mock LINE Webhook Event (Text Message)
    event_data = {
        "destination": "U12345678901234567890123456789012",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "12345678901234",
                    "text": "入住時間"  # Test Question
                },
                "timestamp": 1625665242211,
                "source": {
                    "type": "user",
                    "userId": "U123456deadbeef123456deadbeef1234"
                },
                "replyToken": "00000000000000000000000000000000", # Invalid reply token
                "mode": "active"
            }
        ]
    }
    
    body = json.dumps(event_data, separators=(',', ':')) # LINE uses compact JSON
    signature = generate_signature(secret, body)
    
    headers = {
        'Content-Type': 'application/json',
        'X-Line-Signature': signature
    }

    print("🚀 Sending mock webhook request to http://localhost:5001/callback...")
    try:
        response = requests.post('http://localhost:5001/callback', headers=headers, data=body)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")

        if response.status_code == 200:
            print("✅ Server accepted the request!")
        elif response.status_code == 500:
            print("⚠️ Server returned 500. This is EXPECTED if the Reply Token is invalid.")
            print("   (Because we are trying to reply to a fake token, LINE API rejects it, causing our server to error)")
            print("   This proves the server received and processed the message!")
        else:
            print("❌ Something went wrong.")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to localhost:5001. Is the server running?")

if __name__ == "__main__":
    simulate_webhook()
