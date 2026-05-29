# main.py
from fastapi import FastAPI
from routers import ingest, search, inspect

print("🚀 [MAIN] Iniciando servidor FastAPI - Arquitectura Modular")
app = FastAPI(title="Motor IA - RAG Modular y Seguro")

# Registramos las rutas de cada módulo independiente
app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(inspect.router)

print("✅ [MAIN] Todos los módulos registrados. ¡Listo para recibir peticiones!\n")