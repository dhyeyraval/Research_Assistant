from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime

class Message(BaseModel):
    role: str = Field(..., description="Either 'user' or 'assistant'")
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class AttachedPaper(BaseModel):
    arxiv_id: str
    title: str

class ChatCreate(BaseModel):
    user_id: str
    conversation_name: str = Field(default="New Conversation")

class ChatResponse(BaseModel):
    id: str
    user_id: str
    conversation_name: str
    attached_papers: List[AttachedPaper] = Field(default_factory=list)
    messages: List[Message]
    created_at: datetime