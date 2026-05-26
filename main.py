from fastapi import FastAPI
from routes import router  # Importamos el router que contiene los endpoints

# Inicializamos la aplicación de FastAPI
app = FastAPI(title="Motor IA - RAG Modular Seguro")

# Registramos las rutas del proyecto
app.include_router(router)