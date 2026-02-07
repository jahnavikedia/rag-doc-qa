"""Question answering endpoints — regular and streaming."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from app.models.schemas import QueryRequest, QueryResponse

router = APIRouter(prefix="/query", tags=["Query"])

# Gets set during app startup in main.py
retriever_service = None


@router.post("", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Ask a question against your uploaded documents.

    Retrieves relevant chunks from ChromaDB and generates
    a grounded answer using the LLM.
    """
    if retriever_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    result = retriever_service.ask(
        question=request.question,
        collection=request.collection,
        top_k=request.top_k,
    )

    return QueryResponse(**result)


@router.post("/stream")
async def ask_question_stream(request: QueryRequest):
    """Stream an answer token by token via Server-Sent Events (SSE).

    The frontend receives tokens as they're generated,
    creating the real-time "typing" effect.

    Event types:
        - "sources": The retrieved source chunks (sent first)
        - "token": Individual answer tokens
        - "done": Signals the stream is complete
    """
    if retriever_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    def event_stream():
        for chunk in retriever_service.ask_stream(
            question=request.question,
            collection=request.collection,
            top_k=request.top_k,
        ):
            if isinstance(chunk, dict):
                # First yield is always the sources
                yield f"event: sources\ndata: {json.dumps(chunk)}\n\n"
            else:
                # Subsequent yields are tokens
                yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )