# core/config.py
import os
import chromadb
from google import genai
from dotenv import load_dotenv

print("⚙️ [CONFIG] Cargando variables de entorno y configuraciones base...")
load_dotenv()

# Inicialización de Gemini
print("⚙️ [CONFIG] Inicializando cliente de Google Gemini...")
client = genai.Client()
MODELO_EMBEDDING = "models/gemini-embedding-2"
MODELO_TEXTO = "models/gemini-2.0-flash"

# Inicialización Persistente de ChromaDB
print("⚙️ [CONFIG] Conectando con la base de datos vectorial ChromaDB...")
CHROMA_PATH = "./chroma_db"
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="documentos_taller")

print("✅ [CONFIG] Todos los servicios principales inicializados correctamente.\n")