import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

for model_name in ['gemma-3-27b-it', 'gemma-3-12b-it', 'gemma-3-4b-it', 'gemma-3n-e4b-it']:
    model = genai.GenerativeModel(model_name)
    try:
        response = model.generate_content("Say hello in German. One word only.")
        print(f"[OK] {model_name}: {response.text.strip()}")
        break
    except Exception as e:
        err = str(e)[:150]
        print(f"[FAIL] {model_name}: {err}")
