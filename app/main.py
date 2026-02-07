"""FastAPI application factory with lifespan management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.chunker import Chunker
from app.core.embeddings import EmbeddingProvider
from app.core.vector_store import VectorStore
from app.services.ingestion import IngestionService
from app.services.llm import LLMService
from app.services.retriever import RetrieverService
from app.api.router import api_router
from app.api import documents, query


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic.

    Startup: Initialize all services (load models, connect to DBs).
    Shutdown: Clean up resources.
    """
    print("🚀 Starting up...")

    # Initialize core components
    chunker = Chunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    embedding_provider = EmbeddingProvider()
    vector_store = VectorStore(persist_dir=settings.chroma_persist_dir)
    llm_service = LLMService()

    # Initialize services
    ingestion_service = IngestionService(chunker, embedding_provider, vector_store)
    retriever_service = RetrieverService(embedding_provider, vector_store, llm_service)

    # Inject services into endpoint modules
    documents.ingestion_service = ingestion_service
    documents.vector_store = vector_store
    query.retriever_service = retriever_service

    print("✅ All services initialized!")

    yield  # App runs here

    print("👋 Shutting down...")


app = FastAPI(
    title="DocQA — RAG Document Q&A",
    description="Upload documents and ask questions. Powered by local AI.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(api_router)