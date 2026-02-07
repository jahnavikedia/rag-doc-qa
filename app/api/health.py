"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", response_model=dict)
async def health_check():
    """Check if the API and its dependencies are running.

    This gets wired up with actual dependency checks
    once we connect services in main.py.
    """
    return {
        "status": "healthy",
        "ollama": "not_checked",
        "chromadb": "not_checked",
        "embedding_model": "not_checked",
    }