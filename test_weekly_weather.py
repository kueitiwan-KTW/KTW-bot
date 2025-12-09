import os
from weather_helper import WeatherHelper

# Mock the environment variable for testing if not set
if not os.getenv("CWA_API_KEY"):
    os.environ["CWA_API_KEY"] = "CWA-E41A9CB4-AA6B-4344-8426-32922E2BEA1F"

def test_weekly_forecast():
    helper = WeatherHelper()
    print(f"Testing Weekly Forecast for {helper.location_name}...")
    
    result = helper.get_weekly_forecast()
    print("\n--- Result ---")
    print(result)
    print("--------------")
    
    if "未來一週天氣預報" in result and "資料來源：中央氣象署" in result:
        print("✅ Weekly Forecast Test Successful!")
    else:
        print("❌ Weekly Forecast Test Failed.")

if __name__ == "__main__":
    test_weekly_forecast()
