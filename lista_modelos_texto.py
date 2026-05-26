from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

print("Modelos disponibles en tu cuenta:\n")
for model in client.models.list():
    # Filtramos por nombre para que solo nos muestre los modelos de texto Gemini
    if "gemini" in model.name.lower():
        print(f"- {model.name}")