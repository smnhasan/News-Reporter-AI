"""
routes/embeddings.py
Handles:  POST /v1/embeddings
"""

from fastapi import APIRouter

from schemas import EmbeddingRequest


def make_embeddings_router(server) -> APIRouter:
    """Factory that binds the router to a live *server* instance."""
    router = APIRouter(prefix="/v1", tags=["Embeddings"])

    @router.post("/embeddings")
    async def create_embeddings(request: EmbeddingRequest):
        return await server.embeddings(request)

    return router
