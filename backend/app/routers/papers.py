from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from bson import ObjectId
import httpx
import xml.etree.ElementTree as ET
from typing import List

from app.database.mongo import get_database

from app.services.ingestion import process_and_ingest_paper

router = APIRouter()

# Response Model for Search Results
class PaperSearchResult(BaseModel):
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str

# Request Model for Attaching a Paper
class AttachPaperRequest(BaseModel):
    arxiv_id: str
    title: str

@router.get("/search", response_model=List[PaperSearchResult])
async def search_arxiv(query: str, max_results: int = 5):
    """
    Calls the public arXiv API, parses the XML, and returns clean JSON.
    """
    # Format the query for the arXiv API
    # 1. We keep the + for spaces, but wrap the whole query in %22 (URL encoded double-quotes) for exact matching
    formatted_query = f"%22{query.replace(' ', '+')}%22"
    
    # 2. We add sortBy=relevance to ensure the closest text match rises to the top
    url = f"https://export.arxiv.org/api/query?search_query=all:{formatted_query}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Error reaching arXiv API: {str(e)}")

    # Parse the XML response
    root = ET.fromstring(response.text)
    
    # arXiv XML uses namespaces, which we need to strip or define to find elements easily
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
    
    results = []
    for entry in root.findall('atom:entry', namespace):
        # Extract ID (ArXiv returns a URL like http://arxiv.org/abs/1706.03762v5, we just want the ID)
        id_url = entry.find('atom:id', namespace).text
        arxiv_id = id_url.split('/abs/')[-1]
        
        # Extract Title and clean up newline characters
        title = entry.find('atom:title', namespace).text.replace('\n', ' ').strip()
        
        # Extract Abstract
        abstract = entry.find('atom:summary', namespace).text.strip()
        
        # Extract all Authors
        authors = [author.find('atom:name', namespace).text for author in entry.findall('atom:author', namespace)]
        
        results.append(PaperSearchResult(
            arxiv_id=arxiv_id,
            title=title,
            authors=authors,
            abstract=abstract
        ))
        
    return results

@router.post("/{chat_id}/attach")
async def attach_paper_to_chat(chat_id: str, request: AttachPaperRequest, background_tasks: BackgroundTasks, db=Depends(get_database)):
    """
    Links a selected arXiv ID to a specific chat conversation.
    """
    if not ObjectId.is_valid(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat ID format")

    # Use $addToSet to ensure we don't add the same paper twice to a single chat
    result = await db.chats.find_one_and_update(
        {"_id": ObjectId(chat_id)},
        {"$addToSet": {"attached_papers": {"arxiv_id": request.arxiv_id, "title": request.title}}},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="Chat conversation not found")
    
    background_tasks.add_task(
        process_and_ingest_paper, 
        request.arxiv_id, 
        request.title, 
        "Abstract not provided in this payload", 
        []
    )

    # For Phase 1, we just return the updated list of active IDs
    return {"message": "Paper attached successfully", "attached_papers": result.get("attached_papers", [])}