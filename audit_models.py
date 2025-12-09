import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

load_dotenv()

def audit_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    
    # List of models to test (Common aliases + ones seen in list_models)
    candidates = [
        "gemini-pro",
        "gemini-pro-latest",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-2.0-flash-exp",
        "gemini-2.0-pro-exp-02-05",
        "gemini-exp-1206"
    ]

    print(f"{'Model Name':<30} | {'Status':<10} | {'Response'}")
    print("-" * 80)

    for model_name in candidates:
        try:
            model = genai.GenerativeModel(model_name)
            start = time.time()
            response = model.generate_content("Hi", request_options={'timeout': 10})
            duration = time.time() - start
            
            status = "✅ OK"
            msg = f"{duration:.2f}s"
        except Exception as e:
            error_str = str(e)
            if "404" in error_str:
                status = "❌ 404"
                msg = "Not Found"
            elif "429" in error_str or "ResourceExhausted" in error_str:
                status = "⚠️ Quota"
                msg = "Rate Limited"
            else:
                status = "❌ Error"
                msg = error_str[:40] + "..."
        
        print(f"{model_name:<30} | {status:<10} | {msg}")

if __name__ == "__main__":
    audit_models()
