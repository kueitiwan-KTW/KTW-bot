import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def verify_model():
    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    
    model_name = 'gemini-2.0-pro-exp-02-05'
    print(f"Checking model: {model_name}...")
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, can you hear me?")
        print(f"✅ Success! Response: {response.text}")
    except Exception as e:
        print(f"❌ Failed to generate content: {e}")

if __name__ == "__main__":
    verify_model()
