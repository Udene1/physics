import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("NO GEMINI_API_KEY FOUND")
    exit(1)

genai.configure(api_key=api_key)

print(f"Key: {api_key[:5]}...{api_key[-5:]}")

try:
    print("\nAvailable Models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"LIST MODELS FAILED: {e}")

models_to_test = ["models/gemini-1.5-flash", "models/gemini-2.0-flash-exp", "models/gemini-1.5-flash-8b"]

for model_name in models_to_test:
    print(f"\nTesting {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hi")
        print(f"SUCCESS: {model_name}")
        print(f"Response: {response.text[:20]}...")
    except Exception as e:
        print(f"FAILURE: {model_name} - {e}")
