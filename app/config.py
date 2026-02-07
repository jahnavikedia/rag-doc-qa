"""Application configuration via environment variables."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Ollama (local LLM)
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"

    # Embeddings (local, free)
    embedding_model: str = "all-MiniLM-L6-v2"

    # ChromaDB
    chroma_persist_dir: Path = Path("./data/chroma")

    # Chunking
    chunk_size: int = Field(default=512, ge=100, le=4096)
    chunk_overlap: int = Field(default=50, ge=0, le=512)

    # Retrieval
    top_k: int = Field(default=5, ge=1, le=20)

    # Server
    log_level: str = "info"
    cors_origins: list[str] = ["http://localhost:3000"]
    upload_dir: Path = Path("./uploads")
    max_upload_mb: int = 20


# Singleton — import this from anywhere in the app
settings = Settings()