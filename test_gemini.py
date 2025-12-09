import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY is not set in .env")
        return

    print(f"Checking API Key: {api_key[:5]}...{api_key[-5:]}")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        print("🚀 Sending test request to Gemini...")
        response = model.generate_content("Hello, are you working?")
        
        print(f"✅ Gemini Response: {response.text}")
        print("API Connection Successful!")
        
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")

if __name__ == "__main__":
    test_gemini()
