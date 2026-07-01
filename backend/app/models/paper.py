from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PaperMetadata(BaseModel):
    arxiv_id: str = Field(..., description="Unique arXiv identifier")
    title: str
    authors: List[str]
    abstract: str
    uploaded_at: datetime = Field(default_factory=datetime.now)