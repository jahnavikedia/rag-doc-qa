"""Document upload, list, and delete endpoints."""

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException, Query

from app.models.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DeleteResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents"])

# These get set during app startup in main.py
ingestion_service = None
vector_store = None


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Query(default="default"),
):
    """Upload a PDF document for ingestion.

    The file goes through the full pipeline:
    parse → chunk → embed → store in ChromaDB.
    """
    if ingestion_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    # Save uploaded file to a temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        # Run the ingestion pipeline
        result = ingestion_service.ingest_pdf(
            file_path=tmp_path,
            filename=file.filename,
            collection_name=collection,
        )
        return DocumentUploadResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        # Always clean up the temp file
        tmp_path.unlink(missing_ok=True)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    collection: str = Query(default="default"),
):
    """List all documents in a collection."""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    collections = vector_store.list_collections()

    # Find the requested collection
    for coll in collections:
        if coll["name"] == collection:
            return DocumentListResponse(
                documents=[],  # We'll improve this later with actual doc tracking
                total=coll["count"],
            )

    return DocumentListResponse(documents=[], total=0)


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str,
    collection: str = Query(default="default"),
):
    """Delete a document and all its chunks."""
    if ingestion_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = ingestion_service.delete_document(document_id, collection)
        return DeleteResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))