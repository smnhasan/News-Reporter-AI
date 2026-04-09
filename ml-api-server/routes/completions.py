"""
routes/completions.py
Handles:  POST /v1/completions  (streaming & non-streaming)
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from schemas import CompletionRequest


def make_completions_router(server) -> APIRouter:
    """Factory that binds the router to a live *server* instance."""
    router = APIRouter(prefix="/v1", tags=["Completions"])

    @router.post("/completions")
    async def create_completion(request: CompletionRequest):
        if request.stream:
            return StreamingResponse(
                server.stream_completion(request),
                media_type="text/event-stream",
            )
        return await server.completion(request)

    return router
