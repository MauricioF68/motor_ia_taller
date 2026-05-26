from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from google import genai
import os
import docx  # Para leer archivos .docx de forma nativa
import traceback
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

app = FastAPI(title="Motor IA - Ingesta Robusta")

MODELO = "models/gemini-embedding-2"

def extraer_texto_docx(path):
    doc = docx.Document(path)
    return "\n".join([parrafo.text for parrafo in doc.paragraphs])

@app.post("/ingest/")
async def ingest_document(
    file: UploadFile = File(...),
    group_id: str = Form(...),
    category: str = Form(...)
):
    temp_path = f"temp_{file.filename}"
    try:
        # 1. Guardar archivo temporal
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # 2. Extraer texto plano (El único formato que acepta el modelo de embedding)
        print(f"[1] Extrayendo texto de: {file.filename}")
        texto_limpio = extraer_texto_docx(temp_path)
        
        # 3. Enviar texto plano al modelo de embedding
        print(f"[2] Enviando texto al modelo: {MODELO}")
        response = client.models.embed_content(
            model=MODELO,
            contents=texto_limpio
        )
        
        vector = response.embeddings[0].values
        print(f"[3] Embedding exitoso. Dimensión: {len(vector)}")

        if os.path.exists(temp_path): os.remove(temp_path)

        return {"status": "success", "dimension": len(vector)}

    except Exception as e:
        traceback.print_exc()
        if os.path.exists(temp_path): os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))