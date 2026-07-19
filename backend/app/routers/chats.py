from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime
from typing import List
from google import genai
from google.genai import types

import asyncio
import time

from app.config import GEMINI_API_KEY
from app.database.mongo import get_database
from app.database.vector import get_vector_index
from app.models.chat import ChatCreate, ChatResponse, Message

router = APIRouter()

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# 1. Create a new chat conversation
@router.post("/new", response_model=ChatResponse)
async def create_new_chat(chat_data: ChatCreate, db=Depends(get_database)):
    new_chat = {
        "user_id": chat_data.user_id,
        "conversation_name": chat_data.conversation_name,
        "attached_papers": [],
        "messages": [],
        "created_at": datetime.now()
    }
    
    result = await db.chats.insert_one(new_chat)
    
    return ChatResponse(
        id=str(result.inserted_id),
        user_id=new_chat["user_id"],
        conversation_name=new_chat["conversation_name"],
        attached_papers=new_chat["attached_papers"],
        messages=[],
        created_at=new_chat["created_at"]
    )

# 2. Get all chat conversations for a specific user (for the Sidebar)
@router.get("/user/{user_id}", response_model=List[ChatResponse])
async def get_user_chats(user_id: str, db=Depends(get_database)):
    cursor = db.chats.find({"user_id": user_id}).sort("created_at", -1)
    chats = []
    
    async for doc in cursor:
        chats.append(ChatResponse(
            id=str(doc["_id"]),
            user_id=doc["user_id"],
            conversation_name=doc["conversation_name"],
            attached_papers=doc.get("attached_papers", []),
            messages=[Message(**m) for m in doc["messages"]],
            created_at=doc["created_at"]
        ))
    return chats

# 3. Add a message to an existing conversation (Hybrid RAG + File API)
@router.post("/{chat_id}/message", response_model=List[Message])
async def add_message_to_chat(chat_id: str, message: Message, db=Depends(get_database)):
    start_time = time.perf_counter() # Start timing for performance monitoring

    if not ObjectId.is_valid(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat ID format")
        
    chat = await db.chats.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat conversation not found")
        
    arxiv_ids = [p["arxiv_id"] for p in chat.get("attached_papers", [])]
    
    rag_ids = []
    gemini_file_names = []
    
    # THE CAP (n): Maximum number of papers to process via direct File API
    MAX_DIRECT_FILES = 2 

    if arxiv_ids:
        # --- THE SMART WAITING LOOP ---
        while True:
            cursor = db.papers.find({"arxiv_id": {"$in": arxiv_ids}})
            paper_docs = await cursor.to_list(length=None)
            
            # Count papers that haven't even hit the database yet
            found_ids = {doc["arxiv_id"] for doc in paper_docs}
            missing_count = len(arxiv_ids) - len(found_ids)
            
            # Pending means it's either downloading or uploaded to File API but RAG isn't done
            pending_docs = [doc for doc in paper_docs if doc.get("status") != "completed"]
            total_pending = len(pending_docs) + missing_count
            
            # Check if any pending papers are still downloading (no gemini_file_name yet)
            unready_pending = [doc for doc in pending_docs if not doc.get("gemini_file_name")]
            
            # Logic: If total pending is <= n, AND all of those pending files 
            # have successfully uploaded to Gemini API, we can break the loop!
            if total_pending <= MAX_DIRECT_FILES and len(unready_pending) == 0 and missing_count == 0:
                for doc in paper_docs:
                    if doc.get("status") == "completed":
                        rag_ids.append(doc["arxiv_id"])
                    elif doc.get("gemini_file_name"):
                        gemini_file_names.append(doc["gemini_file_name"])
                break
                
            # If > n papers are pending, or files are still downloading, wait 2 seconds.
            # (Your frontend will just show a loading spinner during this time)
            await asyncio.sleep(2)
            
    # --- ASSEMBLE HYBRID CONTEXT ---
    gemini_contents = []
    
    # 1. Fetch RAG Context for completed papers (Using ASYNC Embed)
    context_text = ""
    if rag_ids:
        try:
            embedding_response = await ai_client.aio.models.embed_content(
                model='gemini-embedding-001',
                contents=message.content,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            pinecone_response = get_vector_index().query(
                vector=embedding_response.embeddings[0].values,
                top_k=5,
                include_metadata=True,
                filter={"arxiv_id": {"$in": rag_ids}}
            )
            chunks = [m["metadata"]["text"] for m in pinecone_response.get("matches", []) if "text" in m.get("metadata", {})]
            context_text = "\n\n".join(chunks)
        except Exception as e:
            print(f"Vector search failed: {str(e)}")

    if context_text:
        gemini_contents.append(
            "You are an expert research assistant. Answer the user's question using the provided relevant text chunks "
            f"extracted from the attached research papers.\n\n--- RELEVANT PAPER CONTEXT ---\n{context_text}\n---------------------------"
        )
    else:
        gemini_contents.append("You are an expert research assistant. Answer the user's question using the attached files.")

    # 2. Add the User's Message
    gemini_contents.append(f"User Question: {message.content}")

    # 3. Add Raw File API Objects for pending papers (Using ASYNC Get)
    for file_name in gemini_file_names:
        try:
            f = await ai_client.aio.files.get(name=file_name)
            gemini_contents.append(f)
        except Exception as e:
            print(f"Could not load file {file_name}: {e}")

    # --- GENERATE & SAVE RESPONSE (Using ASYNC Generate) ---
    try:
        gemini_response = await ai_client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=gemini_contents
        )
        assistant_reply = gemini_response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Generation failed: {str(e)}")

    user_message_dict = message.model_dump()
    user_message_dict["timestamp"] = datetime.utcnow()
    
    assistant_message_dict = {
        "role": "assistant",
        "content": assistant_reply,
        "timestamp": datetime.utcnow()
    }
    
    result = await db.chats.find_one_and_update(
        {"_id": ObjectId(chat_id)},
        {"$push": {"messages": {"$each": [user_message_dict, assistant_message_dict]}}},
        return_document=True
    )

    end_time = time.perf_counter() # End timing for performance monitoring
    execution_time = end_time - start_time
    print(f"Response time = {execution_time} seconds")
        
    return [Message(**m) for m in result["messages"]]