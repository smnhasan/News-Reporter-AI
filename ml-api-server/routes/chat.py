"""
routes/chat.py
Handles:  POST /v1/chat/completions  (streaming & non-streaming)
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from schemas import ChatCompletionRequest


def make_chat_router(server) -> APIRouter:
    """
    Factory that binds the router to a live *server* (CombinedServer) instance.
    This avoids global state while keeping FastAPI's dependency injection clean.
    """
    router = APIRouter(prefix="/v1", tags=["Chat"])

    @router.post("/chat/completions")
    async def create_chat_completion(request: ChatCompletionRequest):
        if request.stream:
            return StreamingResponse(
                server.stream_chat_completion(request),
                media_type="text/event-stream",
            )
        return await server.chat_completion(request)

    return router
