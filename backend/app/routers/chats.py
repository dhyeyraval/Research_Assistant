from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime
from typing import List
from google import genai
from google.genai import types

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

# 3. Add a message to an existing conversation
@router.post("/{chat_id}/message", response_model=List[Message])
async def add_message_to_chat(chat_id: str, message: Message, db=Depends(get_database)):
    if not ObjectId.is_valid(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat ID format")
    
    # Step 1: Fetch the current chat state to see what papers are attached
    chat = await db.chats.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat conversation not found")
        
    attached_papers = chat.get("attached_papers", [])
    arxiv_ids = [p["arxiv_id"] for p in attached_papers]
    
    context_text = ""

    # Step 2: If papers are attached, query Pinecone for relevant context
    if arxiv_ids:
        try:
            # Create a 768-dimensional embedding from the user's question
            embedding_response = ai_client.models.embed_content(
                model='gemini-embedding-001',
                contents=message.content,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            query_vector = embedding_response.embeddings[0].values
            
            # Query Pinecone using a metadata filter limited to this chat's attached papers
            index = get_vector_index()
            pinecone_response = index.query(
                vector=query_vector,
                top_k=5,
                include_metadata=True,
                filter={"arxiv_id": {"$in": arxiv_ids}}
            )
            
            # Extract and stitch text chunks together
            chunks = [
                match["metadata"]["text"] 
                for match in pinecone_response.get("matches", []) 
                if "metadata" in match and "text" in match["metadata"]
            ]
            context_text = "\n\n".join(chunks)
        except Exception as e:
            print(f"Vector search failed: {str(e)}. Proceeding with fallback general generation.")

    # Step 3: Construct the context-infused prompt for Gemini
    if context_text:
        system_instruction = (
            "You are an expert research assistant. Answer the user's question using the provided relevant text chunks "
            "extracted from the attached research papers. If the answer cannot be found completely in the context, use your "
            "general technical knowledge to fill gaps but clearly specify what came from the papers versus general knowledge.\n\n"
            f"--- RELEVANT PAPER CONTEXT ---\n{context_text}\n---------------------------"
        )
    else:
        system_instruction = (
            "You are an expert research assistant. Note: There are currently no research papers attached to this specific "
            "conversation, so please answer the user's question using your overall knowledge base."
        )

    # Step 4: Generate the reply using Gemini 2.5 Flash
    try:
        gemini_response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_instruction}\n\nUser Question: {message.content}"
        )
        assistant_reply = gemini_response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Generation failed: {str(e)}")
        
    # # Convert the incoming message to a dictionary for MongoDB storage
    # message_dict = message.model_dump()
    # message_dict["timestamp"] = datetime.now()
    
    # result = await db.chats.find_one_and_update(
    #     {"_id": ObjectId(chat_id)},
    #     {"$push": {"messages": message_dict}},
    #     return_document=True
    # )
    
    # if not result:
    #     raise HTTPException(status_code=404, detail="Chat conversation not found")
        
    # return [Message(**m) for m in result["messages"]]

    # Step 5: Format both messages and atomically push them to MongoDB
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
        
    return [Message(**m) for m in result["messages"]]