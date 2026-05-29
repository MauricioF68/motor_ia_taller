# routers/ingest.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import docx
import traceback
from core.config import client, collection, MODELO_EMBEDDING

router = APIRouter()

def extraer_texto_docx(path):
    doc = docx.Document(path)
    return "\n".join([parrafo.text for parrafo in doc.paragraphs])

@router.post("/ingest/")
async def ingest_document(
    file: UploadFile = File(...),
    group_id: str = Form(...),
    category: str = Form(...)
):
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        print(f"\n📥 [INGESTA] Procesando archivo: {file.filename} (Grupo: {group_id}, Categoría: {category})")
        texto_limpio = extraer_texto_docx(temp_path)
        
        if not texto_limpio.strip():
            raise ValueError("El archivo Word está vacío o no contiene texto legible.")
        
        print(f"🧠 [INGESTA] Vectorizando texto con {MODELO_EMBEDDING}...")
        response = client.models.embed_content(
            model=MODELO_EMBEDDING,
            contents=texto_limpio
        )
        
        vector = response.embeddings[0].values
        
        # ID Determinista para evitar duplicados y mantener limpieza
        id_documento = f"grupo_{group_id}_categoria_{category}"
        
        print(f"💾 [INGESTA] Ejecutando UPSERT en ChromaDB para el ID: {id_documento}...")
        collection.upsert(
            ids=[id_documento],                     
            embeddings=[vector],                   
            documents=[texto_limpio],                
            metadatas=[{
                "group_id": group_id, 
                "category": category,
                "original_filename": file.filename 
            }]
        )
        
        print(f"✅ [INGESTA] Upsert exitoso. Base de datos vectorial limpia y actualizada.")

        if os.path.exists(temp_path): 
            os.remove(temp_path)

        return {
            "status": "success", 
            "dimension": len(vector),
            "message": "Documento indexado correctamente (Upsert)"
        }

    except Exception as e:
        print("\n❌ [INGESTA] ERROR EN EL PIPELINE !!!")
        traceback.print_exc()
        if os.path.exists(temp_path): 
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))