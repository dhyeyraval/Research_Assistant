from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import auth, chats, papers

from app.database.mongo import connect_to_mongo, close_mongo_connection
from app.database.vector import connect_to_pinecone

# Lifespan context manager handles startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await connect_to_pinecone()
    yield
    await close_mongo_connection()

app = FastAPI(title="Research Assistant API", lifespan=lifespan)

# Setup CORS to allow your React frontend to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include our API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Include the routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chats.router, prefix="/api/chats", tags=["Conversations"])
app.include_router(papers.router, prefix="/api/papers", tags=["Papers"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Research Assistant API. Systems are online."}