from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from app.database.mongo import get_database
from app.models.user import UserCreate, UserResponse

router = APIRouter()

@router.post("/login", response_model=UserResponse)
async def login_or_create_user(user_data: UserCreate, db=Depends(get_database)):
    users_collection = db.users
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"username": user_data.username})
    
    if existing_user:
        # Return existing user (convert MongoDB _id to string)
        return UserResponse(
            id=str(existing_user["_id"]),
            username=existing_user["username"],
            created_at=existing_user["created_at"]
        )
    
    # If not, create a new user
    new_user = {
        "username": user_data.username,
        "created_at": datetime.now()
    }
    result = await users_collection.insert_one(new_user)
    
    return UserResponse(
        id=str(result.inserted_id),
        username=new_user["username"],
        created_at=new_user["created_at"]
    )