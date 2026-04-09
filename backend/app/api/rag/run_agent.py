#!/usr/bin/env python3
"""
run_agent.py
────────────
Interactive CLI demo for the ReActAgent.

Usage
─────
    python run_agent.py                        # interactive REPL
    python run_agent.py "What is machine learning?"  # single query

Environment
───────────
    API_URL     base URL of the local OpenAI-compatible server
                (same as used by the RAG pipeline)

Exit the REPL with Ctrl-C, Ctrl-D, or by typing "exit" / "quit".
"""

import logging
import os
import sys

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
# Quieten noisy third-party loggers
for _noisy in ("httpx", "chromadb", "urllib3", "duckduckgo_search"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

logger = logging.getLogger("run_agent")

# ── import agent ──────────────────────────────────────────────────────────────
try:
    from rag.agent import ReActAgent
except ImportError as e:
    sys.exit(
        f"Import error: {e}\n"
        "Make sure you run this script from the project root:\n"
        "    python run_agent.py\n"
        "and that all dependencies are installed:\n"
        "    pip install duckduckgo-search beautifulsoup4 requests"
    )

# ── helpers ───────────────────────────────────────────────────────────────────
BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║              🤖  ReActAgent  —  Agentic RAG Demo                ║
║                                                                  ║
║  Tools: vector_search · web_search · ingest_url · memo_*        ║
║  Memory: short-term (conversation) + long-term (ChromaDB)       ║
║  Type  'exit' or Ctrl-C to quit.                                 ║
╚══════════════════════════════════════════════════════════════════╝
"""

DIVIDER = "─" * 68


def run_repl(agent: ReActAgent) -> None:
    print(BANNER)
    turn = 0
    while True:
        try:
            query = input("\n💬  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not query:
            continue
        if query.lower() in {"exit", "quit", "q"}:
            print("Bye!")
            break

        turn += 1
        print(f"\n{DIVIDER}")
        print(f"🤖  Agent (turn {turn}):\n")

        try:
            # Stream the final answer
            for chunk in agent.stream(query):
                print(chunk, end="", flush=True)
            print(f"\n{DIVIDER}")
        except KeyboardInterrupt:
            print("\n[Interrupted]")
        except Exception as exc:
            logger.exception("Agent error: %s", exc)
            print(f"[Error: {exc}]")


def run_single(agent: ReActAgent, query: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"Query: {query}")
    print(DIVIDER)
    try:
        for chunk in agent.stream(query):
            print(chunk, end="", flush=True)
        print(f"\n{DIVIDER}")
    except Exception as exc:
        logger.exception("Agent error: %s", exc)
        sys.exit(1)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    api_url = os.getenv("API_URL", "")
    if not api_url:
        print(
            "⚠️  API_URL environment variable is not set.\n"
            "   The agent will attempt to connect to the default endpoint.\n"
            "   Set it with:  export API_URL=https://your-ngrok-url\n"
        )

    logger.info("Initialising ReActAgent …")
    try:
        agent = ReActAgent()
    except Exception as e:
        sys.exit(f"Failed to initialise agent: {e}")

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        run_single(agent, query)
    else:
        run_repl(agent)


if __name__ == "__main__":
    main()
