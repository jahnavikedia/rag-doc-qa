"""Main API router — combines all endpoint groups."""

from fastapi import APIRouter

from app.api import documents, health, query

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(documents.router)
api_router.include_router(query.router)