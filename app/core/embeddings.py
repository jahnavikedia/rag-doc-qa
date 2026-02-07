"""Embedding provider — converts text into numerical vectors.

Uses sentence-transformers to run a model locally.
No API keys needed, completely free.
"""

from sentence_transformers import SentenceTransformer


class EmbeddingProvider:
    """Generates embeddings using a local sentence-transformers model.

    The model is loaded once when this class is created,
    then reused for every embed call.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        print(f"📦 Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"✅ Embedding model loaded! (dimension: {self.dimension})")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Convert a list of texts into embeddings.

        Used during ingestion to embed all chunks of a document.

        Args:
            texts: List of strings to embed.

        Returns:
            List of vectors (each vector is a list of floats).
        """
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Convert a single query string into an embedding.

        Used during querying to embed the user's question.

        Args:
            text: The query string.

        Returns:
            A single vector (list of floats).
        """
        embedding = self.model.encode(text, show_progress_bar=False)
        return embedding.tolist()