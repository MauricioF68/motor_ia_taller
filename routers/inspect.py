# routers/inspect.py
from fastapi import APIRouter, HTTPException
import traceback
from core.config import collection

router = APIRouter()

@router.get("/chroma/inspect")
async def inspect_chroma():
    """Endpoint de auditoría visual para ver qué hay realmente en ChromaDB"""
    try:
        print("\n🔍 [INSPECT] Petición recibida para auditar ChromaDB...")
        data = collection.get(include=["metadatas", "documents"])
        
        registros_legibles = []
        for i in range(len(data["ids"])):
            registros_legibles.append({
                "id_vectorial": data["ids"][i],
                "metadata": data["metadatas"][i] if data["metadatas"] else {},
                "extracto_texto": data["documents"][i][:100] + "..." if data["documents"] else "Sin texto"
            })
            
        print(f"📊 [INSPECT] Se encontraron {len(data['ids'])} registros vectoriales.")
        return {
            "status": "success",
            "total_registros_guardados": len(data["ids"]),
            "registros": registros_legibles
        }
    except Exception as e:
        print("\n❌ [INSPECT] ERROR AL INSPECCIONAR CHROMADB !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))