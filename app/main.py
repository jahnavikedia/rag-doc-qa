"""FastAPI application — the entry point of our backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown.

    Startup: initialize all services (vector store, embeddings, LLM)
    Shutdown: clean up resources
    """
    print(f"🚀 Starting DocQA server...")
    print(f"   LLM: Ollama ({settings.ollama_model})")
    print(f"   Embeddings: {settings.embedding_model}")
    print(f"   Chunk size: {settings.chunk_size}")

    # TODO: We'll initialize our services here soon
    # - Vector store (ChromaDB)
    # - Embedding model (sentence-transformers)
    # - LLM client (Ollama)
    # - Ingestion service
    # - Retriever service

    yield  # App is running and handling requests between startup and shutdown

    print("👋 Shutting down DocQA server...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DocQA — Document Q&A with RAG",
        description=(
            "Upload documents, chunk and embed them into a vector store, "
            "and query them with natural language to get grounded answers."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS — allows our React frontend to talk to this backend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # TODO: We'll add our API routes here
    # app.include_router(api_router)

    return app


# This is what uvicorn runs
app = create_app()