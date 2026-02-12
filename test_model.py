import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# List all available models – this will confirm what's actually accessible
print("=== Available Models ===")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")

print("\n=== Testing gemini-1.5-flash-latest ===")
model = genai.GenerativeModel("gemini-1.5-flash-latest")
response = model.generate_content("Say hello")
print(response.text)