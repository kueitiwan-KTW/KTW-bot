import os
from dotenv import load_dotenv
from weather_helper import WeatherHelper
from datetime import datetime

# Load env to ensure key is present
load_dotenv()

def test_today():
    print("--- Testing Weather Query for Today ---")
    helper = WeatherHelper()
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"Querying for: {today_str}")
    print(f"API Key present: {bool(helper.api_key)}")
    if helper.api_key:
        print(f"API Key prefix: {helper.api_key[:5]}")
    
    result = helper.get_weather_forecast(today_str)
    print(f"Result:\n{result}")

if __name__ == "__main__":
    test_today()
