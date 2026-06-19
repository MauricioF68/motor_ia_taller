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
        
        print("🧠 [RAG] 1. Convirtiendo pregunta a vector...")
        response_emb = client.models.embed_content(
            model=MODELO_EMBEDDING,
            contents=request.pregunta
        )
        vector_pregunta = response_emb.embeddings[0].values

        print(f"🗄️ [RAG] 2. Buscando fragmentos en ChromaDB para el grupo {request.group_id}...")
        
        # Preparar filtro base (siempre por group_id)
        where_filter = {"group_id": {"$eq": request.group_id}}
        
        # Si se envía categoría específica, usamos un $and
        if request.category:
            where_filter = {
                "$and": [
                    {"group_id": {"$eq": request.group_id}},
                    {"category": {"$eq": request.category}}
                ]
            }

        resultados = collection.query(
            query_embeddings=[vector_pregunta],
            n_results=5, # Aumentado a 5 para traer mayor contexto de varios fragmentos
            where=where_filter
        )

        documentos_encontrados = resultados.get("documents", [[]])[0]
        
        if not documentos_encontrados:
            print("⚠️ [RAG] RESULTADO: No existen documentos vectorizados para este filtro.")
            contexto = "" # Dejarlo vacío para que se use solo el agile_context
        else:
            contexto = "\n".join(documentos_encontrados)
            print(f"📝 [RAG] 3. Contexto recuperado ({len(documentos_encontrados)} fragmentos).")

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
Eres un asistente experto y un auditor de proyectos de ingeniería.
Se te proporciona información de un grupo de estudiantes de dos fuentes distintas:
1. **Contexto de Documentos** (extraído de la base de datos vectorial con sus entregables oficiales).
2. **Progreso Ágil** (Backlog y Dailys), el cual recibes como instrucciones de sistema.

Tu objetivo principal es responder a la Consulta de manera clara y precisa basándote en ambas fuentes.
- Si la consulta es de tipo general, utiliza la información de los documentos o del progreso ágil para responder.
- Si la consulta requiere evaluar el avance, realiza un análisis comparativo y crítico cruzando el progreso real (backlog/dailys) con lo planificado (documentos).

Contexto de Documentos:
{contexto}

Consulta a responder: {request.pregunta}
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