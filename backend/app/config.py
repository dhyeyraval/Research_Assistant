import os
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("No MONGO_URI found in .env file")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("No PINECONE_API_KEY found in .env file")
    
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "research-papers")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("No GEMINI_API_KEY found in .env file")