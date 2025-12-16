import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

load_dotenv()

def verify_flash():
    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    
    model_name = 'gemini-flash-latest'
    print(f"Testing model: {model_name}")
    
    model = genai.GenerativeModel(model_name)
    
    print("Sending 5 rapid requests to test Quota...")
    try:
        for i in range(5):
            start = time.time()
            response = model.generate_content(f"Count {i}", request_options={'timeout': 10})
            print(f" Request {i+1}: ✅ Success ({time.time() - start:.2f}s)")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    verify_flash()
