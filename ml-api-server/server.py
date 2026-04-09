"""
server.py
CombinedServer — loads models and exposes async methods called by the route handlers.
FastAPI app construction and route registration live in app.py.
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from typing import Dict, List, Optional, Union

import numpy as np
from fastapi import HTTPException
from huggingface_hub import hf_hub_download
from InstructorEmbedding import INSTRUCTOR
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer

from config import settings
from schemas import ChatCompletionRequest, CompletionRequest, EmbeddingRequest, Message

logger = logging.getLogger(__name__)


class CombinedServer:
    """Loads the LLM and embedding models; exposes async handler methods."""

    def __init__(self):
        cfg = settings

        # ── LLM ──────────────────────────────────────────────────────────────
        logger.info(f"Downloading LLM: {cfg.llm_model_repo}/{cfg.llm_model_file}")
        model_path = hf_hub_download(repo_id=cfg.llm_model_repo, filename=cfg.llm_model_file)
        logger.info(f"LLM downloaded to: {model_path}")

        logger.info("Loading LLM into memory (GPU offload)...")
        self.llm = Llama(
            model_path=model_path,
            n_ctx=cfg.n_ctx,
            n_gpu_layers=cfg.n_gpu_layers,
            verbose=False,
        )
        logger.info("LLM loaded successfully.")

        # ── Embedding — E5 ───────────────────────────────────────────────────
        logger.info(f"Loading embedding model: {cfg.embedding_model_e5_id}")
        self.embedder_e5 = SentenceTransformer(cfg.embedding_model_e5_id)
        logger.info(f"E5 model loaded — dim={cfg.embedding_model_e5_dim}")

        # ── Embedding — Instructor ────────────────────────────────────────────
        logger.info(f"Loading embedding model: {cfg.embedding_model_instructor_id}")
        self.embedder_instructor = INSTRUCTOR(cfg.embedding_model_instructor_id)
        logger.info(f"Instructor model loaded — dim={cfg.embedding_model_instructor_dim}")

        # ── Concurrency primitives ────────────────────────────────────────────
        self.semaphore      = asyncio.Semaphore(cfg.max_requests)
        self.llm_lock       = threading.Lock()
        self.embed_e5_lock  = threading.Lock()
        self.embed_ins_lock = threading.Lock()

        logger.info("CombinedServer initialised.")

    # ── Internal prompt helpers ───────────────────────────────────────────────

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

    async def chat_completion(self, request: ChatCompletionRequest) -> Dict:
        async with self.semaphore:
            try:
                prompt = self._messages_to_prompt(request.messages)
                stops  = self._stop_sequences(request.stop)
                with self.llm_lock:
                    resp = self.llm(
                        prompt,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        stop=stops,
                    )
                text = resp["choices"][0]["text"].strip()
                return {
                    "id":      f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    "object":  "chat.completion",
                    "created": int(time.time()),
                    "model":   request.model,
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                    "usage":   {
                        "prompt_tokens":     len(prompt.split()),
                        "completion_tokens": len(text.split()),
                        "total_tokens":      len(prompt.split()) + len(text.split()),
                    },
                }
            except Exception as e:
                logger.error(f"Chat completion error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def stream_chat_completion(self, request: ChatCompletionRequest):
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

    async def completion(self, request: CompletionRequest) -> Dict:
        async with self.semaphore:
            try:
                stops = self._stop_sequences(request.stop)
                with self.llm_lock:
                    resp = self.llm(
                        request.prompt,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        stop=stops,
                    )
                text = resp["choices"][0]["text"]
                return {
                    "id":      f"cmpl-{uuid.uuid4().hex[:8]}",
                    "object":  "text_completion",
                    "created": int(time.time()),
                    "model":   request.model,
                    "choices": [{"text": text, "index": 0, "finish_reason": "stop"}],
                    "usage":   {
                        "prompt_tokens":     len(request.prompt.split()),
                        "completion_tokens": len(text.split()),
                        "total_tokens":      len(request.prompt.split()) + len(text.split()),
                    },
                }
            except Exception as e:
                logger.error(f"Completion error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def stream_completion(self, request: CompletionRequest):
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

    async def embeddings(self, request: EmbeddingRequest) -> Dict:
        async with self.semaphore:
            try:
                texts: List[str] = [request.input] if isinstance(request.input, str) else request.input
                if not texts:
                    raise HTTPException(status_code=400, detail="'input' must not be empty.")

                model_id = request.model.strip()
                if model_id == settings.embedding_model_instructor_id:
                    vectors    = self._embed_instructor(texts, request.instruction)
                    used_model = settings.embedding_model_instructor_id
                elif model_id in (settings.embedding_model_e5_id, ""):
                    vectors    = self._embed_e5(texts)
                    used_model = settings.embedding_model_e5_id
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Unknown embedding model '{model_id}'. "
                            f"Supported: '{settings.embedding_model_e5_id}', "
                            f"'{settings.embedding_model_instructor_id}'."
                        ),
                    )

                data_list, total_tokens = [], 0
                for idx, (text, vec) in enumerate(zip(texts, vectors)):
                    total_tokens += len(text.split())
                    data_list.append({"object": "embedding", "embedding": vec.tolist(), "index": idx})

                return {
                    "object": "list",
                    "data":   data_list,
                    "model":  used_model,
                    "usage":  {"prompt_tokens": total_tokens, "total_tokens": total_tokens},
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Embedding error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    # ── Low-level encode helpers ──────────────────────────────────────────────

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
