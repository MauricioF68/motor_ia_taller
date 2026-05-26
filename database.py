import chromadb

# Configuramos la ruta persistente
CHROMA_PATH = "./chroma_db"

# Inicializamos el cliente una sola vez al cargar el archivo
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="documentos_taller")

def guardar_vector_en_chroma(filename: str, texto: str, vector: list, group_id: str, category: str):
    """
    Recibe los datos procesados y los inyecta en ChromaDB.
    """
    collection.add(
        ids=[filename],
        embeddings=[vector],
        documents=[texto],
        metadatas=[{
            "group_id": group_id, 
            "category": category
        }]
    )
    return True