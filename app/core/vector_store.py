"""ChromaDB vector store — stores and searches document embeddings.

Wraps ChromaDB with a clean interface for our RAG pipeline.
Supports collection isolation for organizing different document sets.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path


class VectorStore:
    """Persistent ChromaDB vector store.

    Data is saved to disk so it survives server restarts.
    """

    def __init__(self, persist_dir: str | Path):
        """Initialize ChromaDB with persistent storage.

        Args:
            persist_dir: Directory where ChromaDB saves its data.
        """
        persist_dir = Path(persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        print(f"✅ Vector store initialized at {persist_dir}")

    def _get_collection(self, name: str) -> chromadb.Collection:
        """Get or create a collection by name."""
        return self._client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )

    def add_chunks(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        chunk_ids: list[str],
        metadatas: list[dict],
        collection: str = "default",
    ) -> int:
        """Store chunks with their embeddings.

        Called during ingestion after chunking and embedding.

        Args:
            texts: The actual text of each chunk.
            embeddings: The embedding vector for each chunk.
            chunk_ids: Unique ID for each chunk (e.g., "doc123::chunk-0").
            metadatas: Extra info per chunk (document_id, filename, etc.).
            collection: Which collection to store in.

        Returns:
            Number of chunks stored.
        """
        if not texts:
            return 0

        coll = self._get_collection(collection)

        coll.add(
            ids=chunk_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return len(texts)

    def search(
        self,
        query_embedding: list[float],
        collection: str = "default",
        top_k: int = 5,
    ) -> list[dict]:
        """Find the most similar chunks to a query embedding.

        Called during querying to retrieve relevant context.

        Args:
            query_embedding: The embedded question vector.
            collection: Which collection to search.
            top_k: How many results to return.

        Returns:
            List of dicts with keys: text, score, metadata.
            Sorted by relevance (highest score first).
        """
        coll = self._get_collection(collection)

        # Don't search an empty collection
        if coll.count() == 0:
            return []

        results = coll.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, coll.count()),
            include=["documents", "metadatas", "distances"],
        )

        # Convert ChromaDB results into a simpler format
        retrieved = []
        for i in range(len(results["ids"][0])):
            # ChromaDB returns cosine DISTANCE (0 = identical)
            # We convert to SIMILARITY (1 = identical) which is more intuitive
            distance = results["distances"][0][i]
            similarity = 1.0 - distance

            retrieved.append({
                "text": results["documents"][0][i],
                "score": round(similarity, 4),
                "metadata": results["metadatas"][0][i],
            })

        return retrieved

    def delete_document(self, document_id: str, collection: str = "default") -> int:
        """Delete all chunks belonging to a document.

        Args:
            document_id: The document whose chunks to delete.
            collection: Which collection to delete from.

        Returns:
            Number of chunks deleted.
        """
        coll = self._get_collection(collection)

        # Find all chunk IDs for this document
        results = coll.get(
            where={"document_id": document_id},
            include=[],
        )

        if not results["ids"]:
            return 0

        coll.delete(ids=results["ids"])
        return len(results["ids"])

    def list_collections(self) -> list[dict]:
        """List all collections with their chunk counts."""
        collections = self._client.list_collections()
        return [
            {"name": c.name, "count": c.count()}
            for c in collections
        ]

    def heartbeat(self) -> bool:
        """Check if ChromaDB is responsive. Used by health endpoint."""
        try:
            self._client.heartbeat()
            return True
        except Exception:
            return False