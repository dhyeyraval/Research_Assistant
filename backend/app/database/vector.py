from pinecone import Pinecone, ServerlessSpec
from app.config import PINECONE_API_KEY, PINECONE_INDEX_NAME

class VectorDB:
    pc: Pinecone = None
    index = None

vector_db = VectorDB()

async def connect_to_pinecone():
    print("Connecting to Pinecone...")
    vector_db.pc = Pinecone(api_key=PINECONE_API_KEY)
    
    existing_indexes = [index_info["name"] for index_info in vector_db.pc.list_indexes()]
    
    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Index '{PINECONE_INDEX_NAME}' not found. Creating it now (this takes a few seconds)...")
        vector_db.pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=768, # Gemini text-embedding-004 dimension size
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1" # Standard free tier region
            )
        )
        print("Index created successfully!")
        
    vector_db.index = vector_db.pc.Index(PINECONE_INDEX_NAME)
    print("Successfully connected to Pinecone Index!")

def get_vector_index():
    return vector_db.index