"""
memory.py
─────────
Two-tier memory for the agentic system.

ShortTermMemory
    A sliding deque of recent conversation turns (role + content).
    Injected directly into the messages list sent to the LLM.

LongTermMemory
    Persistent memory backed by ChromaDB (the same vector store used by
    the RAG pipeline). Summaries are stored as Documents with
    metadata {"type": "agent_memory"} so they live alongside ingested
    content and are retrieved by the same similarity search.

Memory
    Facade combining both tiers.  The agent only interacts with this class.
"""

import logging
from collections import deque
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

_DEFAULT_SHORT_TERM_TURNS = 20   # keep last N messages


# ── Short-term ────────────────────────────────────────────────────────────────

class ShortTermMemory:
    """
    Sliding window over conversation turns.

    Each turn is stored as (role, content).  The window rolls when
    ``max_turns`` is exceeded so the LLM context stays bounded.
    """

    def __init__(self, max_turns: int = _DEFAULT_SHORT_TERM_TURNS):
        self.max_turns = max_turns
        self._turns: deque[Tuple[str, str]] = deque(maxlen=max_turns)

    # ── write ────────────────────────────────────────────────────
    def add(self, role: str, content: str) -> None:
        self._turns.append((role, content))

    def clear(self) -> None:
        self._turns.clear()

    # ── read ─────────────────────────────────────────────────────
    def as_messages(self) -> List[dict]:
        """Return OpenAI-style message dicts ready to prepend to a prompt."""
        return [{"role": r, "content": c} for r, c in self._turns]

    def __len__(self) -> int:
        return len(self._turns)

    def __repr__(self) -> str:
        return f"ShortTermMemory({len(self)}/{self.max_turns} turns)"


# ── Long-term ─────────────────────────────────────────────────────────────────

class LongTermMemory:
    """
    Persistent memory stored in ChromaDB via the shared Retriever.

    Summaries are ingested as LangChain Documents with
    ``metadata={"source": "agent_memory", "type": "agent_memory"}``
    so they are naturally returned alongside domain documents when the
    agent recalls context.
    """

    def __init__(self, retriever=None):
        self._retriever = retriever

    # ── write ────────────────────────────────────────────────────
    def store(self, content: str, tag: str = "agent_memory") -> bool:
        """
        Persist *content* in the vector store.

        Returns True on success, False on failure.
        """
        if self._retriever is None:
            logger.debug("LongTermMemory: no retriever, skipping store.")
            return False
        if not content.strip():
            return False
        try:
            from langchain_core.documents import Document
            doc = Document(
                page_content=content,
                metadata={"source": tag, "type": "agent_memory"},
            )
            self._retriever.ingest([doc])
            logger.info("LTM stored (%d chars): %s…", len(content), content[:60])
            return True
        except Exception as e:
            logger.error("LTM store failed: %s", e)
            return False

    # ── read ─────────────────────────────────────────────────────
    def recall(self, query: str) -> str:
        """
        Retrieve the most relevant long-term memories for *query*.

        Returns a formatted string, or empty string if nothing found.
        """
        if self._retriever is None:
            return ""
        if not query.strip():
            return ""
        try:
            context, _ = self._retriever.retrieve(query)
            if context and not context.startswith("No relevant"):
                return context
        except Exception as e:
            logger.error("LTM recall failed: %s", e)
        return ""

    def __repr__(self) -> str:
        has = self._retriever is not None
        return f"LongTermMemory(retriever={'attached' if has else 'none'})"


# ── Facade ────────────────────────────────────────────────────────────────────

class Memory:
    """
    Combined short-term + long-term memory facade used by the agent.

    Usage::

        mem = Memory(retriever=my_retriever)

        # after each turn
        mem.add_user("What is X?")
        mem.add_assistant("X is …")

        # build context for next call
        msgs   = mem.short_term_messages()   # inject into messages list
        ltm    = mem.recall("X")             # inject into system prompt

        # persist important facts
        mem.store("Key insight about X: …")
    """

    def __init__(
        self,
        retriever=None,
        max_short_term_turns: int = _DEFAULT_SHORT_TERM_TURNS,
    ):
        self.short_term = ShortTermMemory(max_turns=max_short_term_turns)
        self.long_term  = LongTermMemory(retriever=retriever)

    # ── short-term helpers ────────────────────────────────────────
    def add_user(self, content: str) -> None:
        self.short_term.add("user", content)

    def add_assistant(self, content: str) -> None:
        self.short_term.add("assistant", content)

    def short_term_messages(self) -> List[dict]:
        return self.short_term.as_messages()

    def clear_short_term(self) -> None:
        self.short_term.clear()

    # ── long-term helpers ─────────────────────────────────────────
    def recall(self, query: str) -> str:
        return self.long_term.recall(query)

    def store(self, content: str) -> bool:
        return self.long_term.store(content)

    # ── convenience ───────────────────────────────────────────────
    def snapshot(self, query: str, answer: str) -> None:
        """
        Persist a Q→A pair summary in long-term memory and append the
        turn to short-term memory — one call after each completed turn.
        """
        self.add_user(query)
        self.add_assistant(answer)
        summary = f"User asked: {query[:300]}\nAgent answered: {answer[:500]}"
        self.store(summary)

    def __repr__(self) -> str:
        return f"Memory(short={self.short_term!r}, long={self.long_term!r})"
