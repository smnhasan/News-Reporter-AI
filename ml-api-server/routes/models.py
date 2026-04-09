"""
routes/models.py
Handles:  GET /v1/models
"""

import time
from fastapi import APIRouter
from config import settings

router = APIRouter(prefix="/v1", tags=["Models"])


@router.get("/models")
async def list_models():
    ts = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": settings.llm_model_id,
                "object": "model",
                "created": ts,
                "owned_by": "organization",
                "permission": [],
                "root": settings.llm_model_id,
                "parent": None,
            },
            {
                "id": settings.embedding_model_e5_id,
                "object": "model",
                "created": ts,
                "owned_by": "organization",
                "permission": [],
                "root": settings.embedding_model_e5_id,
                "parent": None,
            },
            {
                "id": settings.embedding_model_instructor_id,
                "object": "model",
                "created": ts,
                "owned_by": "organization",
                "permission": [],
                "root": settings.embedding_model_instructor_id,
                "parent": None,
            },
        ],
    }
