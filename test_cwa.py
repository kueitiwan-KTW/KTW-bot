import os
from weather_helper import WeatherHelper
from datetime import datetime, timedelta

# Mock the environment variable for testing if not set
if not os.getenv("CWA_API_KEY"):
    os.environ["CWA_API_KEY"] = "CWA-E41A9CB4-AA6B-4344-8426-32922E2BEA1F"

def test_cwa_connection():
    helper = WeatherHelper()
    print(f"Testing CWA API with Key: {helper.api_key[:5]}...{helper.api_key[-5:]}")
    
    # Test with tomorrow's date
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Querying weather for: {tomorrow} in {helper.location_name}")
    
    # Temporarily modify helper to print raw data for debugging
    import requests
    params = {
        "Authorization": helper.api_key,
        "format": "JSON",
        "locationName": helper.location_name,
        "elementName": "Wx,MinT,MaxT"
    }
    response = requests.get(helper.base_url, params=params)
    print(f"Raw Response Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Raw Response Keys: {data.keys()}")
        if "records" in data:
            print(f"Records Keys: {data['records'].keys()}")
            locations = data["records"]["Locations"][0]["Location"]
            if locations:
                all_names = [loc.get('LocationName') for loc in locations]
                print(f"All Location Names: {all_names}")
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Raw Text: {response.text[:500]}")

    result = helper.get_weather_forecast(tomorrow)
    print(f"Result: {result}")
    
    if "入住當天" in result:
        print("✅ CWA API Connection Successful!")
    else:
        print("❌ CWA API Connection Failed or No Data.")

if __name__ == "__main__":
    test_cwa_connection()
