from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGO_URI

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def connect_to_mongo():
    print("Connecting to MongoDB...")
    db.client = AsyncIOMotorClient(MONGO_URI)
    print("Successfully connected to MongoDB!")

async def close_mongo_connection():
    print("Closing MongoDB connection...")
    db.client.close()
    print("MongoDB connection closed.")

def get_database():
    # 'research_db' is the name of your database; it will be created automatically
    return db.client.research_db