
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.chat import router as chat_router
from backend.routers.documents import router as documents_router
from backend.routers.ingest import router as ingest_router

app = FastAPI(
    title="Multimodal RAG API",
    description="API for document retrieval and question answering",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the chat endpoint
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(ingest_router)

@app.get("/")
def home():
    return {"message": "Multimodal RAG API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}
