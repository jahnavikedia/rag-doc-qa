"""Request and response schemas — the API contract.

These Pydantic models define exactly what the API accepts
and returns. FastAPI uses them for validation and auto-docs.
"""

from pydantic import BaseModel, Field


# --- Document Schemas ---

class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    document_id: str
    filename: str
    chunk_count: int
    collection: str
    status: str


class DocumentInfo(BaseModel):
    """Info about a stored document."""
    document_id: str
    filename: str
    chunk_count: int


class DocumentListResponse(BaseModel):
    """Response for listing documents."""
    documents: list[DocumentInfo]
    total: int


class DeleteResponse(BaseModel):
    """Response after deleting a document."""
    document_id: str
    collection: str
    status: str


# --- Query Schemas ---

class QueryRequest(BaseModel):
    """Request to ask a question."""
    question: str = Field(..., min_length=1, max_length=1000)
    collection: str = Field(default="default")
    top_k: int = Field(default=5, ge=1, le=20)


class SourceChunk(BaseModel):
    """A retrieved source chunk included in the answer."""
    text: str
    score: float
    metadata: dict


class QueryResponse(BaseModel):
    """Response with the answer and sources."""
    answer: str
    sources: list[SourceChunk]


# --- Health Schemas ---

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    ollama: str
    chromadb: str
    embedding_model: str