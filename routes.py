from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from google import genai
import os
import docx
import traceback
import chromadb
from dotenv import load_dotenv

# 1. Inicialización de entorno y cliente oficial de Google
load_dotenv()
client = genai.Client()

# 2. Configuración persistente y directa de ChromaDB
CHROMA_PATH = "./chroma_db"
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="documentos_taller")

# 3. Inicialización del Router de FastAPI
router = APIRouter()

# Modelos oficiales validados para tu cuenta
MODELO_EMBEDDING = "models/gemini-embedding-2"
# ---> AQUÍ ESTÁ LA CORRECCIÓN: Usamos el modelo 2.5 Flash de tu lista <---
MODELO_TEXTO = "models/gemini-2.5-flash" 

def extraer_texto_docx(path):
    doc = docx.Document(path)
    return "\n".join([parrafo.text for parrafo in doc.paragraphs])

# ==========================================
# ENDPOINT 1: INGESTA DE DOCUMENTOS
# ==========================================
@router.post("/ingest/")
async def ingest_document(
    file: UploadFile = File(...),
    group_id: str = Form(...),
    category: str = Form(...)
):
    temp_path = f"temp_{file.filename}"
    try:
        # Guardar archivo binario temporalmente
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        print(f"\n[1] Extrayendo texto de: {file.filename}")
        texto_limpio = extraer_texto_docx(temp_path)
        
        if not texto_limpio.strip():
            raise ValueError("El archivo Word está vacío o no contiene texto legible.")
        
        print(f"[2] Enviando texto al modelo de embedding: {MODELO_EMBEDDING}")
        response = client.models.embed_content(
            model=MODELO_EMBEDDING,
            contents=texto_limpio
        )
        
        vector = response.embeddings[0].values
        print(f"[3] Embedding exitoso. Dimensión: {len(vector)}")

        print(f"[4] Guardando en ChromaDB (Grupo: {group_id}, Categoría: {category})...")
        collection.add(
            ids=[file.filename],                    
            embeddings=[vector],                   
            documents=[texto_limpio],                
            metadatas=[{"group_id": group_id, "category": category}]
        )
        print("[5] ¡Guardado en ChromaDB exitoso!")

        if os.path.exists(temp_path): 
            os.remove(temp_path)

        return {
            "status": "success", 
            "dimension": len(vector),
            "message": "Documento indexado en BD Vectorial"
        }

    except Exception as e:
        print("\n!!! ERROR EN EL PIPELINE DE INGESTA !!!")
        traceback.print_exc()
        if os.path.exists(temp_path): 
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ENDPOINT 2: BÚSQUEDA Y RESPUESTA (RAG)
# ==========================================
@router.post("/search/")
async def search_document(
    pregunta: str = Form(...),
    group_id: str = Form(...),
    category: str = Form(...)
):
    try:
        print(f"\n--- NUEVA BÚSQUEDA: Grupo {group_id} | Categoría: {category} ---")
        print(f"Pregunta del alumno: {pregunta}")
        
        # 1. Convertir la consulta del usuario en un vector armónico
        print("[1] Convirtiendo la pregunta a vector...")
        response_emb = client.models.embed_content(
            model=MODELO_EMBEDDING,
            contents=pregunta
        )
        vector_pregunta = response_emb.embeddings[0].values

        # 2. Buscar en ChromaDB aplicando las cláusulas de filtrado estricto ($and)
        print("[2] Buscando en ChromaDB con filtros de seguridad...")
        resultados = collection.query(
            query_embeddings=[vector_pregunta],
            n_results=1, # Trae el documento/fragmento más relevante
            where={
                "$and": [
                    {"group_id": {"$eq": group_id}},
                    {"category": {"$eq": category}}
                ]
            }
        )

        documentos_encontrados = resultados["documents"][0]
        
        # Si la consulta de metadatos no arroja coincidencias para ese grupo
        if not documentos_encontrados:
            return {
                "status": "success", 
                "respuesta": "No encontré información sobre este tema para tu grupo en esta categoría."
            }

        # 3. Unificar el contexto recuperado
        contexto = "\n".join(documentos_encontrados)
        print("[3] Documento de contexto encontrado. Generando respuesta analítica...")

        # 4. Construcción del Prompt de confinamiento (Seguridad RAG)
        prompt = f"""
        Eres un asistente experto para estudiantes universitarios de taller de ingeniería. 
        Responde la pregunta basándote ÚNICAMENTE en el siguiente contexto extraído de sus documentos guardados. 
        Si la respuesta no está explícita en el contexto, indica amablemente que no dispones de esa información en los archivos cargados.

        Contexto recuperado de la base de datos:
        {contexto}

        Pregunta del estudiante: {pregunta}
        """

        # 5. Generación de la respuesta textual final
        respuesta_ia = client.models.generate_content(
            model=MODELO_TEXTO,
            contents=prompt
        )
        
        print("[4] ¡Respuesta generada con éxito por Gemini!")

        return {
            "status": "success",
            "respuesta": respuesta_ia.text
        }

    except Exception as e:
        print("\n!!! ERROR EN EL PIPELINE DE BÚSQUEDA !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))