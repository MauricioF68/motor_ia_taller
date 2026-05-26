import os
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar tu API KEY desde el archivo .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: No se encontró la GEMINI_API_KEY en el archivo .env")
    exit()

genai.configure(api_key=api_key)

print("Consultando a Google AI Studio los modelos de Embeddings disponibles para tu cuenta...\n")
print("-" * 50)

# Consultamos todos los modelos y filtramos los que sirven para Embeddings (embedContent)
try:
    for m in genai.list_models():
        if 'embedContent' in m.supported_generation_methods:
            print(f"Modelo Válido Encontrado: {m.name}")
    print("-" * 50)
except Exception as e:
    print(f"Error al consultar la API: {e}")