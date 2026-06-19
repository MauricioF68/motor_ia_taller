# routers/search.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import traceback
from core.config import client, collection, MODELO_EMBEDDING, MODELO_TEXTO
from google.genai import types

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class SearchRequest(BaseModel):
    pregunta: str
    group_id: str
    category: Optional[str] = None
    agile_context: str
    history: List[Message] = []

@router.post("/search/")
async def search_document(request: SearchRequest):
    try:
        print(f"\n🔎 [RAG] --- NUEVA BÚSQUEDA ---")
        print(f"🎯 [RAG] Target -> Grupo: {request.group_id} | Categoría: {request.category}")
        print(f"🗣️ [RAG] Pregunta: '{request.pregunta}'")
        
        contexto = ""
        
        if request.category is not None:
            print("🧠 [RAG] 1. Convirtiendo pregunta a vector...")
            response_emb = client.models.embed_content(
                model=MODELO_EMBEDDING,
                contents=request.pregunta
            )
            vector_pregunta = response_emb.embeddings[0].values

            print("🗄️ [RAG] 2. Buscando fragmentos en ChromaDB (Aplicando filtros estrictos)...")
            resultados = collection.query(
                query_embeddings=[vector_pregunta],
                n_results=1, 
                where={
                    "$and": [
                        {"group_id": {"$eq": request.group_id}},
                        {"category": {"$eq": request.category}}
                    ]
                }
            )

            documentos_encontrados = resultados.get("documents", [[]])[0]
            
            if not documentos_encontrados:
                print("⚠️ [RAG] RESULTADO: No existen documentos vectorizados para este filtro.")
                contexto = "No se encontraron documentos adicionales en la base de datos para este tema."
            else:
                contexto = "\n".join(documentos_encontrados)
                print("📝 [RAG] 3. Contexto recuperado.")
        else:
            print("⏩ [RAG] 1-2. Categoría es nula. Omitiendo búsqueda en ChromaDB.")

        print("📝 [RAG] 3/4. Preparando historial y contexto para el LLM...")
        
        contents = []
        
        # 1. Inyectar el historial anterior
        for msg in request.history:
            role = "user" if msg.role == "user" else "model"
            contents.append(
                types.Content(
                    role=role, 
                    parts=[types.Part.from_text(text=msg.content)]
                )
            )
        
        # 2. Preparar el prompt de la pregunta actual
        if contexto:
            prompt = f"""
Eres un asistente experto para estudiantes universitarios de taller de ingeniería. 
Responde la pregunta basándote en el siguiente contexto extraído de sus documentos guardados, si es relevante. 
Si la respuesta no está explícita en el contexto, indica amablemente que no dispones de esa información en los archivos cargados.

Contexto recuperado de la base de datos:
{contexto}

Pregunta del estudiante: {request.pregunta}
"""
        else:
            prompt = request.pregunta
            
        contents.append(
            types.Content(
                role="user", 
                parts=[types.Part.from_text(text=prompt)]
            )
        )
        
        # 3. Preparar el System Instruction con el Agile Context
        system_instruction_text = request.agile_context if request.agile_context else None
        
        config = types.GenerateContentConfig(
            system_instruction=system_instruction_text
        )

        print("✨ [RAG] Generando respuesta con LLM...")
        respuesta_ia = client.models.generate_content(
            model=MODELO_TEXTO,
            contents=contents,
            config=config
        )
        
        print("✨ [RAG] 4. ¡Respuesta generada con éxito!")

        return {
            "respuesta": respuesta_ia.text
        }

    except Exception as e:
        print("\n❌ [RAG] ERROR EN EL PIPELINE DE BÚSQUEDA !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))