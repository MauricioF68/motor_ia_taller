# services/extractor.py
import docx
import fitz  # Librería PyMuPDF para PDFs
import traceback

print("📂 [SERVICES] Cargando módulo extractor de texto universal...")

def extraer_texto_docx(path: str) -> str:
    """Extrae todo el texto de un documento de Word (.docx)"""
    print("📄 [EXTRACTOR] Extrayendo contenido de archivo Word (.docx)")
    doc = docx.Document(path)
    return "\n".join([parrafo.text for parrafo in doc.paragraphs])

def extraer_texto_txt(path: str) -> str:
    """Extrae el texto de un archivo plano (.txt) con soporte UTF-8 universal"""
    print("📄 [EXTRACTOR] Extrayendo contenido de archivo de Texto Plano (.txt)")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extraer_texto_pdf(path: str) -> str:
    """Extrae el texto seleccionable de un archivo PDF usando PyMuPDF"""
    print("📄 [EXTRACTOR] Extrayendo contenido de archivo PDF (.pdf)")
    doc = fitz.open(path)
    texto_completo = []
    
    for num_pagina in range(len(doc)):
        pagina = doc.load_page(num_pagina)
        texto_completo.append(pagina.get_text())
        
    return "\n".join(texto_completo)

def extraer_texto_universal(path: str, filename: str) -> str:
    """
    Enrutador inteligente: Analiza la extensión del archivo, 
    selecciona el extractor correcto y devuelve el texto limpio.
    """
    extension = filename.lower().split('.')[-1]
    print(f"🔍 [EXTRACTOR] Detectada extensión: .{extension} para el archivo: {filename}")
    
    if extension == 'docx' or extension == 'doc':
        return extraer_texto_docx(path)
    elif extension == 'txt':
        return extraer_texto_txt(path)
    elif extension == 'pdf':
        return extraer_texto_pdf(path)
    else:
        # Si llega un formato extraño que bloqueamos en Laravel pero por si acaso pasa
        raise ValueError(f"El motor de IA no tiene soporte programado para el formato: .{extension}")