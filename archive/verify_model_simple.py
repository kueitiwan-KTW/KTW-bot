import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def verify_simple():
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"API Key Head: {api_key[:5]}...")
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel('gemini-pro-latest')
    print("Sending request to gemini-pro-latest...")
    try:
        response = model.generate_content("Hello")
        print(f"✅ Success: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_simple()
