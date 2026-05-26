from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

# Consultamos los modelos disponibles en tu cuenta
for model in client.models.list():
    if "embedding" in model.name:
        print(f"Modelo encontrado: {model.name}")