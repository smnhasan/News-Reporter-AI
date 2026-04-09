"""
planner.py
──────────
Given a user query, available tools, and optional memory context, the
Planner asks the LLM to produce a short numbered plan *before* the ReAct
loop starts.

The plan is:
  1. embedded in the agent system prompt so the LLM knows what it intends to do.
  2. returned as a List[str] so the caller can log / display it.

The Planner uses the same LLM instance as the agent (no extra API calls
beyond what is already in the loop).
"""

import json
import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

_PLANNER_SYSTEM = """\
You are a planning assistant for an AI research agent.

Given:
  - A user query
  - A list of available tools
  - Optional prior context from memory

Produce a concise, numbered, step-by-step plan that the agent should follow
to answer the query.  Output ONLY a JSON array of short strings — one string
per step.  Do NOT add any text outside the JSON array.

Example output:
["Search the knowledge base for relevant information on X.",
 "If results are insufficient, search the web for X.",
 "Store any important findings in memo.",
 "Synthesise a clear, cited answer."]
"""


class Planner:
    """
    Generates a JSON-array plan before the main ReAct loop.

    Parameters
    ----------
    llm : rag.models.llm.LLM
        The shared LLM instance.
    max_steps : int
        Hint to the LLM about plan length (not enforced, just in the prompt).
    """

    def __init__(self, llm, max_steps: int = 6):
        self.llm = llm
        self.max_steps = max_steps

    def plan(
        self,
        query: str,
        tool_names: List[str],
        memory_context: str = "",
    ) -> List[str]:
        """
        Ask the LLM for a plan and return it as a list of step strings.

        Falls back to a sensible default plan if the LLM fails or returns
        unparseable output.
        """
        tools_str  = ", ".join(f"`{n}`" for n in tool_names)
        memory_str = (
            f"Prior context from memory:\n{memory_context}\n\n"
            if memory_context.strip() else ""
        )

        user_content = (
            f"Available tools: {tools_str}\n\n"
            f"{memory_str}"
            f"User query: {query}\n\n"
            f"Produce a plan with at most {self.max_steps} steps as a JSON array."
        )

        messages = [
            {"role": "system", "content": _PLANNER_SYSTEM},
            {"role": "user",   "content": user_content},
        ]

        try:
            raw = self.llm.generate_response(messages)
            steps = _extract_json_array(raw)
            if steps:
                logger.info("Plan (%d steps): %s", len(steps), steps)
                return steps
            logger.warning("Planner returned unparseable output; using fallback plan.")
        except Exception as e:
            logger.warning("Planner LLM call failed (%s); using fallback plan.", e)

        return _fallback_plan(tool_names)

    def plan_str(
        self,
        query: str,
        tool_names: List[str],
        memory_context: str = "",
    ) -> str:
        """Convenience wrapper that returns the plan as a numbered string."""
        steps = self.plan(query, tool_names, memory_context)
        return "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))


# ── helpers ───────────────────────────────────────────────────────────────────

def _extract_json_array(text: str) -> Optional[List[str]]:
    """Try to find and parse a JSON array anywhere in *text*."""
    # Try direct parse first
    try:
        result = json.loads(text.strip())
        if isinstance(result, list):
            return [str(s) for s in result]
    except json.JSONDecodeError:
        pass

    # Search for first [...] block
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return [str(s) for s in result]
        except json.JSONDecodeError:
            pass

    return None


def _fallback_plan(tool_names: List[str]) -> List[str]:
    """Return a generic plan when the LLM planner fails."""
    steps = []
    if "vector_search" in tool_names:
        steps.append("Search the local knowledge base for relevant information.")
    if "web_search" in tool_names:
        steps.append("If the knowledge base lacks sufficient information, search the web.")
    if "memo_set" in tool_names:
        steps.append("Store key findings in working memory with memo_set.")
    if "ingest_url" in tool_names:
        steps.append("Optionally ingest a promising URL into the knowledge base.")
    steps.append("Synthesise all gathered information into a clear, cited final answer.")
    return steps or ["Answer the query using available tools and knowledge."]
