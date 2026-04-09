"""
pipeline.py
───────────
Unified Pipeline supporting two modes:

  "rag"    — original single-step RAG (retrieve → generate).
             Fast, deterministic, good for simple factual questions.

  "agent"  — full ReAct agentic loop with planning, tool-calling,
             and two-tier memory (short-term + ChromaDB long-term).
             Better for multi-hop, research-style, or open-ended queries.

Both modes share the same Retriever / ChromaDB instance so the knowledge
base is always consistent.

Quick start
───────────
    # Simple RAG (default)
    pipe = Pipeline()
    print(pipe.run("What is photosynthesis?"))

    # Agentic mode
    pipe = Pipeline(mode="agent")
    print(pipe.run("Find recent news on AI safety and summarise key concerns."))

    # Streaming (works in both modes)
    for chunk in pipe.stream("Explain quantum entanglement"):
        print(chunk, end="", flush=True)

    # Switch mode on the fly
    pipe.set_mode("rag")
"""

import logging
from typing import Iterator, List, Literal, Optional

from .models.llm import LLM
from .prompts    import get_chat_prompt, get_standalone_query_generation_prompt
from .retriever  import Retriever

# Agent components (flat imports — same package level)
from .agent       import ReActAgent
from .memory      import Memory
from .planner     import Planner
from .tool_parser import extract_final_answer, parse_tool_calls
from .tools       import build_registry

logger = logging.getLogger(__name__)

PipelineMode = Literal["rag", "agent"]


class Pipeline:
    """
    Unified RAG + Agent pipeline.

    Parameters
    ----------
    mode : "rag" | "agent"
        Operating mode.  Can be changed later with ``set_mode()``.
    retriever : Retriever | None
        Shared Retriever instance.  Created automatically if not supplied.
    max_agent_iterations : int
        Maximum ReAct iterations in agent mode (ignored in rag mode).
    """

    def __init__(
        self,
        mode: PipelineMode = "agent",
        retriever: Optional[Retriever] = None,
        max_agent_iterations: int = 10,
    ):
        # ── Shared components ─────────────────────────────────────
        self.retriever = retriever or Retriever()
        self._mode     = None          # set properly by set_mode() below

        # ── RAG-mode components ───────────────────────────────────
        self.llm     = LLM()
        self.history: List[tuple] = []   # [(role, content), …]

        # ── Agent-mode components (lazy init) ─────────────────────
        self._agent: Optional[ReActAgent] = None
        self._max_agent_iter = max_agent_iterations

        # Apply mode
        self.set_mode(mode)
        logger.info("Pipeline ready | mode=%s", self._mode)

    # ── Mode management ───────────────────────────────────────────────────────

    def set_mode(self, mode: PipelineMode) -> None:
        """Switch between 'rag' and 'agent' modes without losing the retriever."""
        if mode not in ("rag", "agent"):
            raise ValueError(f"mode must be 'rag' or 'agent', got {mode!r}")

        self._mode = mode

        if mode == "agent":
            # Build the agent lazily (shares retriever with RAG side)
            if self._agent is None:
                self._agent = ReActAgent(
                    retriever=self.retriever,
                    max_iterations=self._max_agent_iter,
                )
            logger.info("Switched to AGENT mode")
        else:
            logger.info("Switched to RAG mode")

    @property
    def mode(self) -> str:
        return self._mode

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, query: str) -> str:
        """
        Process *query* and return the response string.

        Delegates to the RAG pipeline or the ReActAgent depending on mode.
        """
        if self._mode == "agent":
            return self._agent.run(query)
        return self._rag_run(query)

    def stream(self, query: str) -> Iterator[str]:
        """
        Process *query* and yield the response token-by-token.

        Works in both modes.
        """
        if self._mode == "agent":
            yield from self._agent.stream(query)
        else:
            yield from self._rag_stream(query)

    def ingest(self, text: str, source_url: str = "manual") -> int:
        """
        Convenience: chunk *text* and add to the vector store.

        Returns the number of chunks ingested.
        """
        docs = self.retriever.create_documents(text, source_url=source_url)
        if docs:
            self.retriever.ingest(docs)
            logger.info("Ingested %d chunks from %s", len(docs), source_url)
        return len(docs) if docs else 0

    def reset_history(self) -> None:
        """Clear the RAG conversation history (agent memory is separate)."""
        self.history.clear()
        logger.info("RAG history cleared")

    # ── RAG mode internals ────────────────────────────────────────────────────
    # Method names kept identical to the original pipeline.py so any existing
    # callers (FastAPI routes, notebooks, tests) continue to work unchanged.

    def _rag_run(self, query: str) -> str:
        standalone = self._generate_standalone_query(query)
        context, _ = self._retrieve_context(standalone)
        response   = self._generate_response(query, context)
        self._update_history(query, response)
        return response

    def _rag_stream(self, query: str) -> Iterator[str]:
        standalone = self._generate_standalone_query(query)
        context, _ = self._retrieve_context(standalone)
        prompt     = get_chat_prompt(query, history=self.history, context=context)

        full_response = ""
        for chunk in self.llm.stream_response(prompt):
            full_response += chunk
            yield chunk

        self._update_history(query, full_response)

    def _generate_standalone_query(self, query: str) -> str:
        """Rewrite query to be context-independent when history exists."""
        if not self.history:
            return query
        prompt = get_standalone_query_generation_prompt(query, history=self.history)
        standalone = self.llm.generate_response(prompt)
        logger.debug("Standalone query: %s", standalone)
        return standalone

    def _retrieve_context(self, standalone_query: str) -> tuple:
        context, url_map = self.retriever.retrieve(standalone_query)
        logger.debug("Retrieved context (%d chars)", len(context))
        return context, url_map

    def _generate_response(self, query: str, context: str) -> str:
        prompt = get_chat_prompt(query, history=self.history, context=context)
        return self.llm.generate_response(prompt)

    def _update_history(self, query: str, response: str) -> None:
        self.history.extend([
            ("user",      query),
            ("assistant", response),
        ])

    # ── Repr ──────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"Pipeline(mode={self._mode!r}, "
            f"history_turns={len(self.history)//2}, "
            f"agent={'attached' if self._agent else 'none'})"
        )