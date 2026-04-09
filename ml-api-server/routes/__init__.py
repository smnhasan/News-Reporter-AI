"""
routes/__init__.py
Registers all API routers onto the FastAPI app instance.
"""

from fastapi import FastAPI

from routes.health  import router as health_router
from routes.models  import router as models_router
from routes.chat    import make_chat_router
from routes.completions import make_completions_router
from routes.embeddings  import make_embeddings_router


def register_routes(app: FastAPI, server) -> None:
    """Attach all routers to *app*, injecting *server* where needed."""
    app.include_router(health_router)
    app.include_router(models_router)
    app.include_router(make_chat_router(server))
    app.include_router(make_completions_router(server))
    app.include_router(make_embeddings_router(server))
