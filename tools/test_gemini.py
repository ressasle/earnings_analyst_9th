import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-2.0-flash-lite')
try:
    response = model.generate_content("Say hello in German.")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
