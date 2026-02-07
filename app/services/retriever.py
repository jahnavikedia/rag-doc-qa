"""Retriever service — the full question-answering pipeline.

Orchestrates: embed question → search vector store → generate answer.
This is the query-time counterpart to the ingestion service.
"""

from app.core.embeddings import EmbeddingProvider
from app.core.vector_store import VectorStore
from app.services.llm import LLMService


class RetrieverService:
    """Handles the full question → answer pipeline."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        llm_service: LLMService,
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.llm_service = llm_service

    def ask(
        self,
        question: str,
        collection: str = "default",
        top_k: int = 5,
    ) -> dict:
        """Ask a question and get a grounded answer.

        Steps:
            1. Embed the question into a vector
            2. Search ChromaDB for the most similar chunks
            3. Send chunks + question to the LLM
            4. Return the answer with source chunks

        Args:
            question: The user's natural language question.
            collection: Which ChromaDB collection to search.
            top_k: Number of chunks to retrieve.

        Returns:
            A dict with the answer, source chunks, and scores.
        """
        # Step 1: Embed the question
        query_embedding = self.embedding_provider.embed_query(question)

        # Step 2: Search for relevant chunks
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            collection=collection,
        )

        if not results:
            return {
                "answer": "No documents found. Please upload some documents first.",
                "sources": [],
            }

        # Step 3: Extract chunk texts for the LLM
        context_chunks = [r["text"] for r in results]

        # Step 4: Generate answer
        answer = self.llm_service.generate(question, context_chunks)

        # Build source info for the response
        sources = [
            {
                "text": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                "score": round(r["score"], 4),
                "metadata": r["metadata"],
            }
            for r in results
        ]

        return {
            "answer": answer,
            "sources": sources,
        }

    def ask_stream(
        self,
        question: str,
        collection: str = "default",
        top_k: int = 5,
    ):
        """Stream an answer token by token.

        Same retrieval steps as ask(), but streams the LLM response.
        Yields a sources dict first, then individual tokens.

        Args:
            question: The user's question.
            collection: Which collection to search.
            top_k: Number of chunks to retrieve.

        Yields:
            First yield: dict with "sources" key
            Subsequent yields: individual token strings
        """
        # Steps 1-2: Embed and search (same as ask)
        query_embedding = self.embedding_provider.embed_query(question)

        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            collection=collection,
        )

        if not results:
            yield {"sources": []}
            yield "No documents found. Please upload some documents first."
            return

        context_chunks = [r["text"] for r in results]

        # Yield sources first so frontend can show them
        sources = [
            {
                "text": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                "score": round(r["score"], 4),
                "metadata": r["metadata"],
            }
            for r in results
        ]
        yield {"sources": sources}

        # Step 3: Stream the answer
        for token in self.llm_service.generate_stream(question, context_chunks):
            yield token