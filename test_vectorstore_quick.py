
"""Quick test — store chunks and search them."""

from app.core.embeddings import EmbeddingProvider
from app.core.vector_store import VectorStore

# Initialize both components
embeddings = EmbeddingProvider()
store = VectorStore(persist_dir="./data/test_chroma")

# Simulate 3 document chunks
chunks = [
    "The refund policy allows returns within 30 days of purchase.",
    "Employees receive 20 days of paid time off per year.",
    "Our office is located in San Francisco, California.",
]

# Embed the chunks
chunk_embeddings = embeddings.embed_texts(chunks)

# Store them in ChromaDB
store.add_chunks(
    texts=chunks,
    embeddings=chunk_embeddings,
    chunk_ids=["doc1::chunk-0", "doc1::chunk-1", "doc1::chunk-2"],
    metadatas=[
        {"document_id": "doc1", "chunk_index": 0},
        {"document_id": "doc1", "chunk_index": 1},
        {"document_id": "doc1", "chunk_index": 2},
    ],
)
print(f"Stored {len(chunks)} chunks\n")

# Now search with a question
question = "How do I get a refund?"
query_vector = embeddings.embed_query(question)
results = store.search(query_embedding=query_vector, top_k=3)

print(f"Question: '{question}'")
print(f"Results (ranked by relevance):\n")
for i, result in enumerate(results):
    print(f"  [{i}] Score: {result['score']}")
    print(f"      Text: {result['text']}")
    print()