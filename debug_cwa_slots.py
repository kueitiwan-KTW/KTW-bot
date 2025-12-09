import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CWA_API_KEY")
LOCATION = "車城鄉"
# F-D0047-035 is Weekly (12-hour intervals)
URL_WEEKLY = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-035"

def inspect_slots():
    if not API_KEY:
        print("Error: CWA_API_KEY not set")
        return

    params = {
        "Authorization": API_KEY,
        "format": "JSON",
        "locationName": LOCATION,
        "elementName": "天氣現象"
    }

    print(f"Querying {URL_WEEKLY} for {LOCATION}...")
    try:
        response = requests.get(URL_WEEKLY, params=params)
        response.raise_for_status()
        data = response.json()
        
        locations = data["records"]["Locations"][0]["Location"]
        target = next((loc for loc in locations if loc["LocationName"] == LOCATION), None)
        
        if not target:
            print("Location not found.")
            return

        weather_element = next((elem for elem in target["WeatherElement"] if elem["ElementName"] == "天氣現象"), None)
        if not weather_element:
            print("Element '天氣現象' not found.")
            # Print available elements
            print(f"Available: {[e['ElementName'] for e in target['WeatherElement']]}")
            return
            
        print(f"Element: {weather_element['ElementName']}")
        
        print("\n--- Available Time Slots ---")
        now = datetime.now()
        print(f"Current System Time: {now}")
        
        for slot in weather_element["Time"]:
            start = slot["StartTime"]
            end = slot["EndTime"]
            # Check structure of ElementValue
            # Usually [{"Weather": "...", "WeatherCode": "..."}]
            val = slot["ElementValue"][0]["Weather"]
            print(f"Slot: {start} ~ {end} | {val}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_slots()
