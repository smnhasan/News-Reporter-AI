"""
tools.py
────────
Tool definitions and the ToolRegistry.

Available tools
───────────────
  vector_search   — query local ChromaDB knowledge base
  web_search      — DuckDuckGo search (no API key needed)
  ingest_url      — fetch a URL and add its text to the vector store
  memo_set        — store an ephemeral key→value in working memory
  memo_get        — retrieve a value from working memory
  memo_list       — list all key→value pairs in working memory

Each tool is declared with a schema string that the LLM reads in its
system prompt so it knows exactly what parameters to pass.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ToolParam:
    type: str
    description: str
    required: bool = True


@dataclass
class Tool:
    name: str
    description: str
    params: Dict[str, ToolParam]
    fn: Callable

    # ── Schema string shown to the LLM ───────────────────────────
    def schema_str(self) -> str:
        lines = [f"### `{self.name}`", f"{self.description}"]
        if self.params:
            lines.append("Parameters:")
            for pname, p in self.params.items():
                req = "required" if p.required else "optional"
                lines.append(f"  - `{pname}` ({p.type}, {req}): {p.description}")
        else:
            lines.append("Parameters: none")
        return "\n".join(lines)

    def __call__(self, **kwargs) -> str:
        try:
            return str(self.fn(**kwargs))
        except Exception as e:
            logger.exception("Tool '%s' raised: %s", self.name, e)
            return f"[Tool error — {self.name}]: {e}"


# ── Registry ──────────────────────────────────────────────────────────────────

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> "ToolRegistry":
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s", tool.name)
        return self  # fluent

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def names(self) -> List[str]:
        return list(self._tools.keys())

    def all_schemas(self) -> str:
        """Full schema block to embed in the system prompt."""
        return "\n\n".join(t.schema_str() for t in self._tools.values())


# ── Factory ───────────────────────────────────────────────────────────────────

def build_registry(retriever=None) -> ToolRegistry:
    """
    Instantiate all tools and return a populated ToolRegistry.

    Parameters
    ----------
    retriever : rag.retriever.Retriever | None
        Pass the shared Retriever so vector_search and ingest_url share
        the same ChromaDB client.
    """
    registry = ToolRegistry()

    # ── 1. vector_search ─────────────────────────────────────────
    def _vector_search(query: str) -> str:
        if retriever is None:
            return "VectorStore unavailable (no retriever injected)."
        try:
            context, url_map = retriever.retrieve(query)
            if not context or context.startswith("No relevant"):
                return "No relevant documents found in the knowledge base."
            urls = "\n".join(f"  [{k}] {v}" for k, v in url_map.items())
            return f"{context}\nSources:\n{urls}" if urls else context
        except Exception as e:
            return f"Vector search error: {e}"

    registry.register(Tool(
        name="vector_search",
        description=(
            "Search the local knowledge base (ChromaDB) for documents "
            "relevant to the query. Use this first before searching the web."
        ),
        params={
            "query": ToolParam("str", "Natural-language search query."),
        },
        fn=_vector_search,
    ))

    # ── 2. web_search ────────────────────────────────────────────
    def _web_search(query: str, max_results: int = 5) -> str:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return (
                "duckduckgo-search is not installed. "
                "Run: pip install duckduckgo-search"
            )
        try:
            max_results = int(max_results)
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return "No web results found."
            parts = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "(no title)")
                url   = r.get("href",  "")
                body  = r.get("body",  "")
                parts.append(f"[{i}] {title}\n    URL: {url}\n    {body}")
            return "\n\n".join(parts)
        except Exception as e:
            return f"Web search error: {e}"

    registry.register(Tool(
        name="web_search",
        description=(
            "Search the web using DuckDuckGo. No API key required. "
            "Use when the knowledge base lacks the needed information "
            "or when you need current/recent data."
        ),
        params={
            "query":       ToolParam("str", "Search query."),
            "max_results": ToolParam("int", "Number of results (default 5).", required=False),
        },
        fn=_web_search,
    ))

    # ── 3. ingest_url ────────────────────────────────────────────
    def _ingest_url(url: str) -> str:
        if retriever is None:
            return "Retriever unavailable — cannot ingest."
        try:
            import requests as _req
            from bs4 import BeautifulSoup
        except ImportError:
            return "Missing dependencies: pip install requests beautifulsoup4"
        try:
            resp = _req.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            # Remove script / style noise
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            text = text[:10_000]  # cap at 10 KB
            if not text.strip():
                return f"No text content extracted from {url}."
            docs = retriever.create_documents(text, source_url=url)
            if not docs:
                return f"Text extracted but no chunks created from {url}."
            retriever.ingest(docs)
            return f"Ingested {len(docs)} chunks from {url} into the knowledge base."
        except Exception as e:
            return f"Ingest error for {url}: {e}"

    registry.register(Tool(
        name="ingest_url",
        description=(
            "Fetch a web page, extract its text content, and add it to the "
            "local knowledge base. Useful to permanently store a source found "
            "via web_search so it can be retrieved later."
        ),
        params={
            "url": ToolParam("str", "Full URL (including https://) to fetch and ingest."),
        },
        fn=_ingest_url,
    ))

    # ── 4. memo_set / memo_get / memo_list (ephemeral KV store) ──
    # Single dict shared by all three closures within this call to build_registry
    _memo: Dict[str, str] = {}

    def _memo_set(key: str, value: str) -> str:
        _memo[key.strip()] = value
        return f"Stored memo['{key}']."

    def _memo_get(key: str) -> str:
        val = _memo.get(key.strip())
        if val is None:
            return f"No entry for key '{key}'. Current keys: {list(_memo.keys())}"
        return val

    def _memo_list() -> str:
        if not _memo:
            return "Working memory is empty."
        return "\n".join(f"  {k!r}: {v}" for k, v in _memo.items())

    registry.register(Tool(
        name="memo_set",
        description=(
            "Store an intermediate result or note in working memory "
            "under a key. Persists for the duration of this agent session."
        ),
        params={
            "key":   ToolParam("str", "Unique identifier for this piece of information."),
            "value": ToolParam("str", "The value / note to store."),
        },
        fn=_memo_set,
    ))

    registry.register(Tool(
        name="memo_get",
        description="Retrieve a previously stored value from working memory by key.",
        params={
            "key": ToolParam("str", "The key to look up."),
        },
        fn=_memo_get,
    ))

    registry.register(Tool(
        name="memo_list",
        description="List all key-value pairs currently in working memory.",
        params={},
        fn=_memo_list,
    ))

    logger.info("ToolRegistry built with tools: %s", registry.names())
    return registry
