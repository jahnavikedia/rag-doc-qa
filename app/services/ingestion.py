"""Ingestion service — the full document upload pipeline.

Orchestrates: PDF parsing → chunking → embedding → vector storage.
This is the "conveyor belt" connecting all the core components.
"""

import uuid
from pathlib import Path

from app.config import settings
from app.core.chunker import Chunker
from app.core.embeddings import EmbeddingProvider
from app.core.vector_store import VectorStore
from app.utils.pdf_parser import extract_text_from_pdf


class IngestionService:
    """Manages the full document ingestion pipeline."""

    def __init__(
        self,
        chunker: Chunker,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ):
        self.chunker = chunker
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    def ingest_pdf(
        self,
        file_path: Path,
        filename: str,
        collection_name: str = "default",
    ) -> dict:
        """Run the full ingestion pipeline on a PDF.

        Steps:
            1. Extract text from PDF (direct or OCR)
            2. Chunk the text into smaller pieces
            3. Embed each chunk into a vector
            4. Store chunks + vectors in ChromaDB

        Args:
            file_path: Path to the uploaded PDF file.
            filename: Original filename (for metadata).
            collection_name: Which ChromaDB collection to store in.

        Returns:
            A dict with document_id, chunk_count, and status.
        """
        # Generate a unique ID for this document
        document_id = str(uuid.uuid4())

        # Step 1: Parse
        print(f"📄 Step 1/4: Extracting text from {filename}...")
        text = extract_text_from_pdf(file_path)

        # Step 2: Chunk
        print(f"✂️  Step 2/4: Chunking text ({len(text)} chars)...")
        chunks = self.chunker.chunk(text)
        print(f"   → {len(chunks)} chunks created")

        # Step 3: Embed
        print(f"🧮 Step 3/4: Embedding {len(chunks)} chunks...")
        embeddings = self.embedding_provider.embed_texts(chunks)

        # Step 4: Store
        print(f"💾 Step 4/4: Storing in collection '{collection_name}'...")
        metadata = [
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        # Generate unique IDs for each chunk
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]

        self.vector_store.add_chunks(
            texts=chunks,
            embeddings=embeddings,
            chunk_ids=chunk_ids,
            metadatas=metadata,
            collection=collection_name,
        )

        result = {
            "document_id": document_id,
            "filename": filename,
            "chunk_count": len(chunks),
            "collection": collection_name,
            "status": "success",
        }

        print(f"✅ Ingestion complete: {len(chunks)} chunks stored for '{filename}'")
        return result

    def delete_document(
        self, document_id: str, collection_name: str = "default"
    ) -> dict:
        """Remove all chunks for a document from the vector store.

        Args:
            document_id: The UUID assigned during ingestion.
            collection_name: Which collection to delete from.

        Returns:
            A dict with the deletion status.
        """
        self.vector_store.delete_document(document_id, collection_name)

        return {
            "document_id": document_id,
            "collection": collection_name,
            "status": "deleted",
        }