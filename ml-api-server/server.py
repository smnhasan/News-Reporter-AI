"""
GPT-OSS-20B + Multilingual-E5-Large + Instructor-Large
OpenAI-Compatible FastAPI Server

Supports serving via:
  - ngrok tunnel (USE_NGROK=true)
  - localhost only (USE_NGROK=false)
"""

import asyncio
import threading
import time
import json
import os
from typing import Optional, List, Dict, Any, Union
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
from sentence_transformers import SentenceTransformer
from InstructorEmbedding import INSTRUCTOR
import uvicorn
import logging
import requests as http_requests
import atexit
from datetime import datetime, timedelta
import uuid
import numpy as np

from config import settings

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ── Model constants ───────────────────────────────────────────────────────────
LLM_MODEL_REPO  = settings.llm_model_repo
LLM_MODEL_FILE  = settings.llm_model_file
LLM_MODEL_ID    = settings.llm_model_id

EMBEDDING_MODEL_E5_ID       = settings.embedding_model_e5_id
EMBEDDING_MODEL_E5_DIM      = settings.embedding_model_e5_dim

EMBEDDING_MODEL_INSTRUCTOR_ID  = settings.embedding_model_instructor_id
EMBEDDING_MODEL_INSTRUCTOR_DIM = settings.embedding_model_instructor_dim

DEFAULT_EMBEDDING_MODEL_ID = EMBEDDING_MODEL_E5_ID


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str    = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    model: str                            = Field(default=LLM_MODEL_ID)
    messages: List[Message]               = Field(...)
    temperature: Optional[float]          = Field(default=0.7,  ge=0.0, le=2.0)
    max_tokens: Optional[int]             = Field(default=500,  ge=1)
    stream: Optional[bool]                = Field(default=False)
    top_p: Optional[float]                = Field(default=1.0,  ge=0.0, le=1.0)
    frequency_penalty: Optional[float]    = Field(default=0.0,  ge=-2.0, le=2.0)
    presence_penalty: Optional[float]     = Field(default=0.0,  ge=-2.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = Field(default=None)


class CompletionRequest(BaseModel):
    model: str                            = Field(default=LLM_MODEL_ID)
    prompt: str                           = Field(...)
    temperature: Optional[float]          = Field(default=0.7,  ge=0.0, le=2.0)
    max_tokens: Optional[int]             = Field(default=500,  ge=1)
    stream: Optional[bool]                = Field(default=False)
    top_p: Optional[float]                = Field(default=1.0,  ge=0.0, le=1.0)
    stop: Optional[Union[str, List[str]]] = Field(default=None)


class EmbeddingRequest(BaseModel):
    model: str                    = Field(default=DEFAULT_EMBEDDING_MODEL_ID)
    input: Union[str, List[str]]  = Field(..., description="Text or list of texts to embed")
    encoding_format: Optional[str]= Field(default="float")
    dimensions: Optional[int]     = Field(default=None)
    user: Optional[str]           = Field(default=None)
    instruction: Optional[str]    = Field(default=None)


# ── Core server class ─────────────────────────────────────────────────────────

class CombinedServer:
    def __init__(
        self,
        llm_model_name: str  = LLM_MODEL_REPO,
        llm_model_file: str  = LLM_MODEL_FILE,
        n_ctx: int           = 10048,
        n_gpu_layers: int    = -1,
        max_concurrent_requests: int = 3,
    ):
        logger.info(f"Downloading LLM: {llm_model_name}/{llm_model_file}")
        model_path = hf_hub_download(repo_id=llm_model_name, filename=llm_model_file)
        logger.info(f"LLM downloaded to: {model_path}")

        logger.info("Loading LLM into memory (GPU offload)...")
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            verbose=False,
        )
        logger.info("LLM loaded successfully.")

        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_E5_ID}")
        self.embedder_e5 = SentenceTransformer(EMBEDDING_MODEL_E5_ID)
        logger.info(f"E5 embedding model loaded — dim={EMBEDDING_MODEL_E5_DIM}")

        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_INSTRUCTOR_ID}")
        self.embedder_instructor = INSTRUCTOR(EMBEDDING_MODEL_INSTRUCTOR_ID)
        logger.info(f"Instructor embedding model loaded — dim={EMBEDDING_MODEL_INSTRUCTOR_DIM}")

        self.semaphore      = asyncio.Semaphore(max_concurrent_requests)
        self.llm_lock       = threading.Lock()
        self.embed_e5_lock  = threading.Lock()
        self.embed_ins_lock = threading.Lock()

        self.app = FastAPI(
            title="GPT-OSS-20B + Multilingual-E5 + Instructor-Large OpenAI-Compatible API",
            version="2.0.0",
        )
        self._setup_routes()
        logger.info("Server initialised.")

    # ── Route setup ───────────────────────────────────────────────────────────

    def _setup_routes(self):

        @self.app.get("/")
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

        @self.app.get("/health")
        async def health_check():
            return {
                "status":               "healthy",
                "llm_model":            LLM_MODEL_ID,
                "embedding_model_e5":   EMBEDDING_MODEL_E5_ID,
                "embedding_dim_e5":     EMBEDDING_MODEL_E5_DIM,
                "embedding_model_ins":  EMBEDDING_MODEL_INSTRUCTOR_ID,
                "embedding_dim_ins":    EMBEDDING_MODEL_INSTRUCTOR_DIM,
                "backend":              "llama-cpp-python + sentence-transformers + InstructorEmbedding",
            }

        @self.app.get("/v1/models")
        async def list_models():
            ts = int(time.time())
            return {
                "object": "list",
                "data": [
                    {"id": LLM_MODEL_ID,                  "object": "model", "created": ts, "owned_by": "organization", "permission": [], "root": LLM_MODEL_ID,                  "parent": None},
                    {"id": EMBEDDING_MODEL_E5_ID,          "object": "model", "created": ts, "owned_by": "organization", "permission": [], "root": EMBEDDING_MODEL_E5_ID,          "parent": None},
                    {"id": EMBEDDING_MODEL_INSTRUCTOR_ID,  "object": "model", "created": ts, "owned_by": "organization", "permission": [], "root": EMBEDDING_MODEL_INSTRUCTOR_ID,  "parent": None},
                ],
            }

        @self.app.post("/v1/chat/completions")
        async def create_chat_completion(request: ChatCompletionRequest):
            if request.stream:
                return StreamingResponse(
                    self._stream_chat_completion(request),
                    media_type="text/event-stream",
                )
            return await self._chat_completion_response(request)

        @self.app.post("/v1/completions")
        async def create_completion(request: CompletionRequest):
            if request.stream:
                return StreamingResponse(
                    self._stream_completion(request),
                    media_type="text/event-stream",
                )
            return await self._completion_response(request)

        @self.app.post("/v1/embeddings")
        async def create_embeddings(request: EmbeddingRequest):
            return await self._embedding_response(request)

    # ── Prompt helpers ────────────────────────────────────────────────────────

    def _messages_to_prompt(self, messages: List[Message]) -> str:
        parts = []
        for msg in messages:
            if msg.role == "system":
                parts.append(f"<|system|>\n{msg.content}")
            elif msg.role == "user":
                parts.append(f"<|user|>\n{msg.content}<|end|>")
            elif msg.role == "assistant":
                parts.append(f"<|start|>assistant<|channel|>final<|message|>\n{msg.content}<|end|>")
        parts.append("<|start|>assistant<|channel|>final<|message|>\n")
        return "\n".join(parts)

    def _stop_sequences(self, stop: Optional[Union[str, List[str]]]) -> List[str]:
        defaults = ["<|end|>", "<|user|>"]
        if stop is None:
            return defaults
        if isinstance(stop, str):
            return defaults + [stop]
        return defaults + stop

    # ── Chat completion ───────────────────────────────────────────────────────

    async def _chat_completion_response(self, request: ChatCompletionRequest) -> Dict:
        async with self.semaphore:
            try:
                prompt = self._messages_to_prompt(request.messages)
                stops  = self._stop_sequences(request.stop)
                with self.llm_lock:
                    resp = self.llm(prompt, max_tokens=request.max_tokens, temperature=request.temperature, top_p=request.top_p, stop=stops)
                text = resp["choices"][0]["text"].strip()
                return {
                    "id":      f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    "object":  "chat.completion",
                    "created": int(time.time()),
                    "model":   request.model,
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                    "usage":   {"prompt_tokens": len(prompt.split()), "completion_tokens": len(text.split()), "total_tokens": len(prompt.split()) + len(text.split())},
                }
            except Exception as e:
                logger.error(f"Chat completion error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _stream_chat_completion(self, request: ChatCompletionRequest):
        async with self.semaphore:
            try:
                prompt  = self._messages_to_prompt(request.messages)
                stops   = self._stop_sequences(request.stop)
                cid     = f"chatcmpl-{uuid.uuid4().hex[:8]}"
                created = int(time.time())
                yield f"data: {json.dumps({'id': cid, 'object': 'chat.completion.chunk', 'created': created, 'model': request.model, 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': ''}, 'finish_reason': None}]})}\n\n"
                with self.llm_lock:
                    for output in self.llm(prompt, max_tokens=request.max_tokens, temperature=request.temperature, top_p=request.top_p, stop=stops, stream=True):
                        token = output["choices"][0]["text"]
                        yield f"data: {json.dumps({'id': cid, 'object': 'chat.completion.chunk', 'created': created, 'model': request.model, 'choices': [{'index': 0, 'delta': {'content': token}, 'finish_reason': None}]})}\n\n"
                yield f"data: {json.dumps({'id': cid, 'object': 'chat.completion.chunk', 'created': created, 'model': request.model, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Chat stream error: {e}")
                yield f"data: {json.dumps({'error': {'message': str(e), 'type': 'internal_error'}})}\n\n"

    # ── Text completion ───────────────────────────────────────────────────────

    async def _completion_response(self, request: CompletionRequest) -> Dict:
        async with self.semaphore:
            try:
                stops = self._stop_sequences(request.stop)
                with self.llm_lock:
                    resp = self.llm(request.prompt, max_tokens=request.max_tokens, temperature=request.temperature, top_p=request.top_p, stop=stops)
                text = resp["choices"][0]["text"]
                return {
                    "id":      f"cmpl-{uuid.uuid4().hex[:8]}",
                    "object":  "text_completion",
                    "created": int(time.time()),
                    "model":   request.model,
                    "choices": [{"text": text, "index": 0, "finish_reason": "stop"}],
                    "usage":   {"prompt_tokens": len(request.prompt.split()), "completion_tokens": len(text.split()), "total_tokens": len(request.prompt.split()) + len(text.split())},
                }
            except Exception as e:
                logger.error(f"Completion error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _stream_completion(self, request: CompletionRequest):
        async with self.semaphore:
            try:
                stops   = self._stop_sequences(request.stop)
                cid     = f"cmpl-{uuid.uuid4().hex[:8]}"
                created = int(time.time())
                with self.llm_lock:
                    for output in self.llm(request.prompt, max_tokens=request.max_tokens, temperature=request.temperature, top_p=request.top_p, stop=stops, stream=True):
                        token = output["choices"][0]["text"]
                        yield f"data: {json.dumps({'id': cid, 'object': 'text_completion', 'created': created, 'model': request.model, 'choices': [{'text': token, 'index': 0, 'finish_reason': None}]})}\n\n"
                yield f"data: {json.dumps({'id': cid, 'object': 'text_completion', 'created': created, 'model': request.model, 'choices': [{'text': '', 'index': 0, 'finish_reason': 'stop'}]})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Completion stream error: {e}")
                yield f"data: {json.dumps({'error': {'message': str(e), 'type': 'internal_error'}})}\n\n"

    # ── Embeddings ────────────────────────────────────────────────────────────

    async def _embedding_response(self, request: EmbeddingRequest) -> Dict:
        async with self.semaphore:
            try:
                texts: List[str] = [request.input] if isinstance(request.input, str) else request.input
                if not texts:
                    raise HTTPException(status_code=400, detail="'input' must not be empty.")
                model_id = request.model.strip()
                if model_id == EMBEDDING_MODEL_INSTRUCTOR_ID:
                    vectors    = self._embed_instructor(texts, request.instruction)
                    used_model = EMBEDDING_MODEL_INSTRUCTOR_ID
                elif model_id in (EMBEDDING_MODEL_E5_ID, ""):
                    vectors    = self._embed_e5(texts)
                    used_model = EMBEDDING_MODEL_E5_ID
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unknown embedding model '{model_id}'. Supported: '{EMBEDDING_MODEL_E5_ID}', '{EMBEDDING_MODEL_INSTRUCTOR_ID}'.",
                    )
                data_list    = []
                total_tokens = 0
                for idx, (text, vec) in enumerate(zip(texts, vectors)):
                    total_tokens += len(text.split())
                    data_list.append({"object": "embedding", "embedding": vec.tolist(), "index": idx})
                return {"object": "list", "data": data_list, "model": used_model, "usage": {"prompt_tokens": total_tokens, "total_tokens": total_tokens}}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Embedding error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def _embed_e5(self, texts: List[str]) -> np.ndarray:
        with self.embed_e5_lock:
            return self.embedder_e5.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def _embed_instructor(self, texts: List[str], instruction: Optional[str] = None) -> np.ndarray:
        instr = instruction or "Represent the sentence: "
        pairs = [[instr, t] for t in texts]
        with self.embed_ins_lock:
            vecs = self.embedder_instructor.encode(pairs)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return vecs / norms
