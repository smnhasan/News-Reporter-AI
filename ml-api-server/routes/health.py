"""
routes/health.py
Handles:  GET /
          GET /health
"""

from fastapi import APIRouter
from config import settings

router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    return {
        "message": "GPT-OSS-20B + Multilingual-E5 + Instructor-Large OpenAI-Compatible API",
        "endpoints": {
            "chat":        "/v1/chat/completions",
            "completions": "/v1/completions",
            "embeddings":  "/v1/embeddings",
            "models":      "/v1/models",
            "health":      "/health",
        },
    }


@router.get("/health")
async def health_check():
    return {
        "status":              "healthy",
        "llm_model":           settings.llm_model_id,
        "embedding_model_e5":  settings.embedding_model_e5_id,
        "embedding_dim_e5":    settings.embedding_model_e5_dim,
        "embedding_model_ins": settings.embedding_model_instructor_id,
        "embedding_dim_ins":   settings.embedding_model_instructor_dim,
        "backend":             "llama-cpp-python + sentence-transformers + InstructorEmbedding",
    }
