import os
import httpx
import tempfile
import pypdf
import uuid
import asyncio
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY
from app.database.vector import get_vector_index
from app.database.mongo import get_database

# Initialize the new Google GenAI Client
ai_client = genai.Client(api_key=GEMINI_API_KEY)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    """Splits long text into overlapping chunks for better vector search context."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

async def process_and_ingest_paper(arxiv_id: str, title: str, abstract: str, authors: list):
    db = get_database()
    index = get_vector_index()
    
    existing_paper = await db.papers.find_one({"arxiv_id": arxiv_id})
    if existing_paper and existing_paper.get("status") == "completed":
        print(f"Paper {arxiv_id} already fully ingested. Skipping.")
        return True

    print(f"Starting hybrid ingestion for {arxiv_id}...")
    
    await db.papers.update_one(
        {"arxiv_id": arxiv_id},
        {"$set": {"status": "downloading", "title": title, "authors": authors}},
        upsert=True
    )

    pdf_url = f"https://export.arxiv.org/pdf/{arxiv_id}"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_path = tmp_file.name

    try:
        async with httpx.AsyncClient(follow_redirects=True) as http_client:
            response = await http_client.get(pdf_url, timeout=30.0)
            response.raise_for_status()
            with open(tmp_path, "wb") as f:
                f.write(response.content)

        # 3. ASYNC Upload to Gemini
        print("Uploading PDF to Gemini File API for hybrid access...")
        uploaded_file = await ai_client.aio.files.upload(file=tmp_path)
        
        await db.papers.update_one(
            {"arxiv_id": arxiv_id},
            {"$set": {"status": "pending", "gemini_file_name": uploaded_file.name}}
        )

        # 4. CPU-Offloaded Text Extraction (prevents server freezing)
        def extract_text_sync(path):
            text = ""
            with open(path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text

        full_text = await asyncio.to_thread(extract_text_sync, tmp_path)

        # 5. ASYNC Visual Extraction
        print("Generating visual summaries...")
        prompt = "Analyze this research paper. Identify all figures, graphs, and tables. For each one, write a detailed summary. If there are no figures, output 'No visual data found.'"
        
        vision_response = await ai_client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, prompt]
        )
        
        # 6. Chunking and ASYNC Embedding
        text_chunks = chunk_text(full_text)
        if "No visual data found" not in vision_response.text:
            text_chunks.append(f"VISUAL DATA SUMMARIES:\n{vision_response.text}")

        vectors_to_upsert = []
        for i, chunk in enumerate(text_chunks):
            embedding_response = await ai_client.aio.models.embed_content(
                model='gemini-embedding-001',
                contents=chunk,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            
            vector_id = f"{arxiv_id}-chunk-{i}"
            metadata = {"arxiv_id": arxiv_id, "text": chunk}
            
            vectors_to_upsert.append({
                "id": vector_id,
                "values": embedding_response.embeddings[0].values,
                "metadata": metadata
            })

            if len(vectors_to_upsert) >= 50:
                index.upsert(vectors=vectors_to_upsert)
                vectors_to_upsert = []
                
        if vectors_to_upsert:
            index.upsert(vectors=vectors_to_upsert)

        await db.papers.update_one(
            {"arxiv_id": arxiv_id},
            {"$set": {"status": "completed"}}
        )
        print(f"Successfully finished Pinecone RAG ingestion for {arxiv_id}!")
        return True

    except Exception as e:
        print(f"Failed to ingest paper: {str(e)}")
        raise e
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)