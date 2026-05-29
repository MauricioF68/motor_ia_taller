# routers/ingest.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import traceback
from core.config import client, collection, MODELO_EMBEDDING
# IMPORTAMOS NUESTRO SERVICIO
from services.extractor import extraer_texto_universal

router = APIRouter()

@router.post("/ingest/")
async def ingest_document(
    file: UploadFile = File(...),
    group_id: str = Form(...),
    category: str = Form(...)
):
    temp_path = f"temp_{file.filename}"
    try:
        # 1. Guardar el archivo binario temporalmente en el disco del servidor
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        print(f"\n📥 [INGESTA] Petición HTTP POST recibida para: {file.filename}")
        print(f"🎯 [INGESTA] Destino -> Grupo: {group_id} | Categoría: {category}")
        
        # 2. LLAMAMOS AL SERVICIO: Extracción universal delegada
        texto_limpio = extraer_texto_universal(temp_path, file.filename)
        
        # Validación de seguridad: Asegurarse de que el extractor de verdad obtuvo texto legible
        if not texto_limpio or not texto_limpio.strip():
            raise ValueError(
                f"El archivo '{file.filename}' no contiene texto legible. "
                f"Asegúrate de que no esté vacío o de que no sea un PDF escaneado (imagen)."
            )
        
        # 3. Vectorización cognitiva con Gemini
        print(f"🧠 [INGESTA] Solicitando embeddings a Gemini para {len(texto_limpio)} caracteres...")
        response = client.models.embed_content(
            model=MODELO_EMBEDDING,
            contents=texto_limpio
        )
        vector = response.embeddings[0].values
        
        # 4. ID Determinista para asegurar el funcionamiento del patrón Upsert
        id_documento = f"grupo_{group_id}_categoria_{category}"
        
        print(f"💾 [INGESTA] Sincronizando en ChromaDB (ID: {id_documento})...")
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
        
        print(f"✅ [INGESTA] Sincronización exitosa. El motor está listo para responder preguntas de este archivo.")

        # Limpieza obligatoria del archivo temporal
        if os.path.exists(temp_path): 
            os.remove(temp_path)

        return {
            "status": "success", 
            "dimension": len(vector),
            "message": f"Documento .{file.filename.split('.')[-1]} indexado exitosamente (Upsert Modular)"
        }

    except Exception as e:
        print("\n❌ [INGESTA] FATAL ERROR EN EL ROUTER DE INGESTA !!!")
        traceback.print_exc()
        if os.path.exists(temp_path): 
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))