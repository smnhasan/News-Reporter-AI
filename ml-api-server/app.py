"""
app.py
FastAPI application factory.
Separating app creation from the entrypoint makes the app importable
for testing tools (pytest, httpx AsyncClient) without launching a server.
"""

from fastapi import FastAPI

from routes import register_routes


def create_app(server) -> FastAPI:
    """
    Build and return a configured FastAPI instance.

    Parameters
    ----------
    server : CombinedServer
        A fully initialised server instance whose handler methods are
        injected into the route factories.
    """
    app = FastAPI(
        title="GPT-OSS-20B + Multilingual-E5 + Instructor-Large OpenAI-Compatible API",
        version="2.0.0",
        description=(
            "OpenAI-compatible API serving GPT-OSS-20B via llama-cpp-python "
            "alongside multilingual-e5-large and instructor-large embedding models."
        ),
    )

    register_routes(app, server)
    return app
