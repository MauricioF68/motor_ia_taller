# routers/search.py
from fastapi import APIRouter, Form, HTTPException
import traceback
from core.config import client, collection, MODELO_EMBEDDING, MODELO_TEXTO

router = APIRouter()

@router.post("/search/")
async def search_document(
    pregunta: str = Form(...),
    group_id: str = Form(...),
    category: str = Form(...)
):
    try:
        print(f"\n🔎 [RAG] --- NUEVA BÚSQUEDA ---")
        print(f"🎯 [RAG] Target -> Grupo: {group_id} | Categoría: {category}")
        print(f"🗣️ [RAG] Pregunta: '{pregunta}'")
        
        print("🧠 [RAG] 1. Convirtiendo pregunta a vector...")
        response_emb = client.models.embed_content(
            model=MODELO_EMBEDDING,
            contents=pregunta
        )
        vector_pregunta = response_emb.embeddings[0].values

        print("🗄️ [RAG] 2. Buscando fragmentos en ChromaDB (Aplicando filtros estrictos)...")
        resultados = collection.query(
            query_embeddings=[vector_pregunta],
            n_results=1, 
            where={
                "$and": [
                    {"group_id": {"$eq": group_id}},
                    {"category": {"$eq": category}}
                ]
            }
        )

        documentos_encontrados = resultados["documents"][0]
        
        if not documentos_encontrados:
            print("⚠️ [RAG] RESULTADO: No existen documentos vectorizados para este filtro.")
            return {
                "status": "success", 
                "respuesta": "No encontré información sobre este tema para tu grupo en esta categoría."
            }

        contexto = "\n".join(documentos_encontrados)
        print("📝 [RAG] 3. Contexto recuperado. Generando respuesta con LLM...")

        prompt = f"""
        Eres un asistente experto para estudiantes universitarios de taller de ingeniería. 
        Responde la pregunta basándote ÚNICAMENTE en el siguiente contexto extraído de sus documentos guardados. 
        Si la respuesta no está explícita en el contexto, indica amablemente que no dispones de esa información en los archivos cargados.

        Contexto recuperado de la base de datos:
        {contexto}

        Pregunta del estudiante: {pregunta}
        """

        respuesta_ia = client.models.generate_content(
            model=MODELO_TEXTO,
            contents=prompt
        )
        
        print("✨ [RAG] 4. ¡Respuesta generada con éxito!")

        return {
            "status": "success",
            "respuesta": respuesta_ia.text
        }

    except Exception as e:
        print("\n❌ [RAG] ERROR EN EL PIPELINE DE BÚSQUEDA !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))