# 📄 DocQA — RAG Document Q&A

A full-stack **Retrieval-Augmented Generation (RAG)** system that lets you upload PDF documents and ask questions about them in natural language. Answers are grounded in your documents with source citations — no hallucination.

**100% free and local.** No API keys, no cloud services. Everything runs on your machine.

---

## ✨ Features

- **Upload PDFs** — Regular or scanned (OCR support via Tesseract)
- **Ask questions in natural language** — Get grounded answers from your documents
- **Source citations** — See exactly which document chunks informed the answer
- **Streaming responses** — Real-time token-by-token answers (like ChatGPT)
- **Anti-hallucination** — LLM only answers from document context, admits when it doesn't know
- **Semantic search** — Finds relevant content by meaning, not just keywords ("money back" matches "refund policy")
- **Dark-themed chat UI** — Clean React frontend with smooth animations
- **Dockerized** — Full Docker Compose setup with backend, frontend, and nginx proxy

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   React      │     │  FastAPI     │     │   Ollama     │
│   Frontend   │────▶│  Backend     │────▶│  (Local LLM) │
│   (Chat UI)  │     │  + RAG Engine│     │  Llama 3.2   │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
               ┌────▼─────┐  ┌─────▼────┐
               │ Document  │  │ ChromaDB │
               │ Processor │  │ (Vector  │
               │ (Chunker) │─▶│  Store)  │
               └───────────┘  └──────────┘
```

### RAG Pipeline

**Ingestion (once per document):**

```
Upload PDF → Extract text (PyMuPDF / OCR) → Chunk (recursive splitting) → Embed (sentence-transformers) → Store (ChromaDB)
```

**Querying (per question):**

```
Question → Embed → Similarity search → Retrieve top-K chunks → LLM generates grounded answer → Stream to frontend
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | FastAPI + Uvicorn | Async API with auto-generated docs |
| Vector Store | ChromaDB | Local persistent vector database |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | 384-dim semantic embeddings, runs locally |
| LLM | Ollama + Llama 3.2 | Local inference, no API keys needed |
| PDF Parsing | PyMuPDF + pytesseract | Regular + scanned PDF support |
| Frontend | React 18 | Streaming chat UI with dark theme |
| Deployment | Docker Compose + Nginx | Containerized multi-service setup |
| Validation | Pydantic v2 | Request/response validation + settings |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) installed
- [Tesseract](https://github.com/tesseract-ocr/tesseract) installed (optional, for scanned PDFs)

### Option 1: Run with Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/rag-doc-qa.git
cd rag-doc-qa

# Make sure Ollama is running and has the model
ollama pull llama3.2

# Build and start all services
docker compose up --build -d
```

Open `http://localhost:3000` — upload a PDF and start asking questions!

### Option 2: Run Locally

**1. Backend setup:**

```bash
git clone https://github.com/YOUR_USERNAME/rag-doc-qa.git
cd rag-doc-qa

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
```

**2. Pull the LLM model:**

```bash
ollama pull llama3.2
```

**3. Start the backend:**

```bash
uvicorn app.main:app --reload --port 8001
```

API docs available at `http://localhost:8001/docs`

**4. Start the frontend (new terminal):**

```bash
cd frontend
npm install
npm start
```

Open `http://localhost:3000` — upload a PDF and start asking questions!

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/documents/upload` | Upload and ingest a PDF |
| `GET` | `/api/v1/documents` | List ingested documents |
| `DELETE` | `/api/v1/documents/{doc_id}` | Remove a document and its chunks |
| `POST` | `/api/v1/query` | Ask a question, get a full answer |
| `POST` | `/api/v1/query/stream` | Stream an answer token-by-token (SSE) |
| `GET` | `/api/v1/health` | Health check with dependency status |

### Example: Ask a question via curl

```bash
curl -X POST http://localhost:8001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund policy?", "top_k": 5}'
```

---

## 📁 Project Structure

```
rag-doc-qa/
├── app/
│   ├── main.py              # FastAPI app + service initialization
│   ├── config.py            # Pydantic settings from .env
│   ├── api/                 # HTTP endpoints
│   │   ├── router.py        # Route aggregator (/api/v1)
│   │   ├── documents.py     # Upload / list / delete
│   │   ├── query.py         # Question answering + streaming
│   │   └── health.py        # Health check
│   ├── core/                # RAG building blocks
│   │   ├── chunker.py       # Recursive text splitting with overlap
│   │   ├── embeddings.py    # sentence-transformers wrapper
│   │   └── vector_store.py  # ChromaDB wrapper
│   ├── services/            # Business logic orchestration
│   │   ├── ingestion.py     # Full upload pipeline
│   │   ├── retriever.py     # Full query pipeline
│   │   └── llm.py           # Ollama LLM with anti-hallucination prompt
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response models
│   └── utils/
│       └── pdf_parser.py    # PDF text extraction + OCR fallback
├── frontend/                # React chat UI
│   ├── src/
│   │   ├── App.js           # Main chat component
│   │   └── App.css          # Dark theme styling
│   ├── Dockerfile           # Multi-stage build (Node → Nginx)
│   └── nginx.conf           # SPA routing + API proxy
├── docker-compose.yml       # Multi-service orchestration
├── Dockerfile               # Backend container
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## ⚙️ Design Decisions

### Why these matter (interview context)

1. **Fully local stack** — No API keys or paid services. sentence-transformers for embeddings, Ollama for LLM, ChromaDB for storage. Everything runs on the user's machine for privacy and zero cost.

2. **Provider abstraction** — LLM and embedding providers are isolated in separate classes. Swapping Ollama for OpenAI or Claude is a one-file change — no refactoring needed.

3. **Recursive chunking with overlap** — Splits text at natural boundaries (paragraphs → sentences → words) with configurable overlap (~50 chars). Preserves semantic coherence while ensuring no context is lost at chunk edges.

4. **Direct extraction + OCR fallback** — Tries fast text extraction first via PyMuPDF. Falls back to Tesseract OCR only for scanned pages. Regular PDFs stay fast (~1ms/page), scanned pages pay the OCR cost only when needed.

5. **Anti-hallucination system prompt** — LLM is explicitly instructed to answer only from provided context chunks and say "I don't have enough information" when context is insufficient. Tested and verified.

6. **Cosine distance → similarity conversion** — ChromaDB returns distance (0 = identical), we convert to similarity (1 = identical) for intuitive scoring in the API response.

7. **Streaming via SSE** — Server-Sent Events deliver tokens in real-time. Sources are sent first so the frontend can display them immediately while the answer streams in.

8. **Model loaded once at startup** — The embedding model loads in `__init__` (~3-5 sec) and is reused for all requests (milliseconds each). Avoids the performance hit of loading per request.

9. **Dependency injection** — Services receive their dependencies through constructors, making them testable and swappable. The ingestion service doesn't know or care which embedding provider it's using.

10. **Docker Compose** — Three-service architecture (backend, frontend, nginx) with persistent volumes for ChromaDB data. Nginx proxies API calls and handles SPA routing.

---

## 🔧 Configuration

All settings are loaded from `.env` via Pydantic Settings with validation:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.2` | Which Ollama model to use |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | ChromaDB storage location |
| `CHUNK_SIZE` | `512` | Max characters per chunk (100-4096) |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks (0-512) |
| `TOP_K` | `5` | Number of chunks to retrieve per query (1-20) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model |

---

## 📈 Scaling Considerations

This project is designed for local use. For production scale:

| Current | Production Alternative |
|---------|----------------------|
| ChromaDB (local) | Pinecone / Weaviate (managed, distributed) |
| Ollama (local LLM) | OpenAI / Claude API (faster, higher quality) |
| sentence-transformers (local) | OpenAI embeddings API (higher quality) |
| Single process | Multiple Uvicorn workers + async task queue |
| File-based storage | Redis cache for repeated queries |

The provider abstraction pattern makes these swaps straightforward — change one class, not the whole app.

---

## 📝 License

MIT
