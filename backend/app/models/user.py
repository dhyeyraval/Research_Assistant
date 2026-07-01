from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime