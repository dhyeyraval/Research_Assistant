import os
import httpx
import tempfile
import pypdf
import uuid
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
    
    # 1. Deduplication Check
    existing_paper = await db.papers.find_one({"arxiv_id": arxiv_id})
    if existing_paper:
        print(f"Paper {arxiv_id} already exists in Vector DB. Skipping ingestion.")
        return True

    print(f"Starting ingestion for {arxiv_id}...")
    pdf_url = f"https://export.arxiv.org/pdf/{arxiv_id}"
    
    # Create a temporary file to hold the PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_path = tmp_file.name

    try:
        # 2. Download the PDF
        async with httpx.AsyncClient(follow_redirects=True) as http_client:
            response = await http_client.get(pdf_url, timeout=30.0)
            response.raise_for_status()
            with open(tmp_path, "wb") as f:
                f.write(response.content)

        # 3. Extract standard text using PyPDF2
        full_text = ""
        with open(tmp_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

        # 4. Extract visual summaries using Gemini File API
        print("Uploading PDF to Gemini for visual analysis...")
        uploaded_file = ai_client.files.upload(file=tmp_path)
        
        prompt = """
        Analyze this research paper. Identify all figures, graphs, and tables. 
        For each one, write a highly detailed text summary describing the data, trends, axes, and key takeaways. 
        If there are no figures or tables, simply output 'No visual data found.'
        """
        
        vision_response = ai_client.models.generate_content(
            model='gemini-2.5-flash', # We use Flash for fast, cheap visual parsing
            contents=[uploaded_file, prompt]
        )
        visual_summaries = vision_response.text

        # 5. Chunk and Combine Data
        print("Chunking text and generating embeddings...")
        text_chunks = chunk_text(full_text)
        if "No visual data found" not in visual_summaries:
            text_chunks.append(f"VISUAL DATA SUMMARIES:\n{visual_summaries}")

        # 6. Embed and Upload to Pinecone in batches
        vectors_to_upsert = []
        for i, chunk in enumerate(text_chunks):
            # Generate 768-dimensional embedding
            embedding_response = ai_client.models.embed_content(
                model='gemini-embedding-001',
                contents=chunk,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            
            vector_id = f"{arxiv_id}-chunk-{i}"
            metadata = {
                "arxiv_id": arxiv_id,
                "text": chunk,
                "type": "figure_summary" if i == len(text_chunks)-1 else "text"
            }
            
            vectors_to_upsert.append({
                "id": vector_id,
                "values": embedding_response.embeddings[0].values,
                "metadata": metadata
            })

            # Upload in batches of 50 to avoid payload limits
            if len(vectors_to_upsert) >= 50:
                index.upsert(vectors=vectors_to_upsert)
                vectors_to_upsert = []
                
        # Upload any remaining vectors
        if vectors_to_upsert:
            index.upsert(vectors=vectors_to_upsert)

        # 7. Save to MongoDB
        await db.papers.insert_one({
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "ingested_at": os.time() if hasattr(os, 'time') else None # Optional timestamp
        })
        print(f"Successfully ingested {arxiv_id}!")
        return True

    except Exception as e:
        print(f"Failed to ingest paper: {str(e)}")
        raise e
        
    finally:
        # Cleanup temp file and Gemini cloud file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        try:
            ai_client.files.delete(name=uploaded_file.name)
        except:
            pass