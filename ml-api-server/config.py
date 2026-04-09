"""
Configuration — reads from environment variables or a .env file.
Copy .env.example to .env and fill in your values before running.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── Serving ──────────────────────────────────────────────────────────────
    host: str       = Field(default="0.0.0.0",  description="Uvicorn bind host")
    port: int       = Field(default=8000,        description="Uvicorn bind port")

    # ── Ngrok ─────────────────────────────────────────────────────────────────
    use_ngrok: bool          = Field(default=False, description="Set true to expose via ngrok tunnel")
    ngrok_authtoken: str     = Field(default="",    description="Your ngrok auth token (required when use_ngrok=true)")

    # ── LLM ──────────────────────────────────────────────────────────────────
    llm_model_repo: str  = Field(default="ggml-org/gpt-oss-20b-GGUF")
    llm_model_file: str  = Field(default="gpt-oss-20b-mxfp4.gguf")
    llm_model_id: str    = Field(default="gpt-oss-20b")
    n_ctx: int           = Field(default=10048)
    n_gpu_layers: int    = Field(default=-1,  description="-1 = offload all layers to GPU")
    max_requests: int    = Field(default=3,   description="Max concurrent requests (semaphore)")

    # ── Embedding models ──────────────────────────────────────────────────────
    embedding_model_e5_id: str          = Field(default="intfloat/multilingual-e5-large")
    embedding_model_e5_dim: int         = Field(default=1024)
    embedding_model_instructor_id: str  = Field(default="hkunlp/instructor-large")
    embedding_model_instructor_dim: int = Field(default=768)

    # ── HuggingFace ───────────────────────────────────────────────────────────
    hf_token: str = Field(default="", description="Optional HuggingFace token for faster downloads")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
