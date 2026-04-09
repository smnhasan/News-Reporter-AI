"""
agent.py
────────
ReActAgent for pp/api/rag/ flat package structure.

Imports use single-dot relative paths (all siblings in same directory).
"""

import logging
from typing import Iterator, List, Optional

from .models.llm   import LLM
from .retriever    import Retriever
from .memory       import Memory
from .planner      import Planner
from .tool_parser  import extract_final_answer, has_final_answer, parse_tool_calls
from .tools        import ToolRegistry, build_registry

logger = logging.getLogger(__name__)

_MAX_ITERATIONS = 10

_AGENT_SYSTEM = """\
You are an intelligent research assistant equipped with tools and memory.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AVAILABLE TOOLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tool_schemas}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW TO CALL A TOOL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Emit a tool call using this EXACT format:

<tool_call>{{"name": "tool_name", "arguments": {{"param": "value"}}}}</tool_call>

You will receive the result in <tool_result>…</tool_result>.
You may call multiple tools across iterations.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW TO FINISH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
When you have gathered enough information, emit:

<final_answer>
Your complete markdown answer here. Cite sources as [Document N].
</final_answer>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLAN FOR THIS QUERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{plan}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEMORY CONTEXT  (from previous sessions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{memory_context}

Think step-by-step. Follow the plan. Be thorough yet concise.
"""


class ReActAgent:
    """
    ReAct-style agent with planning and two-tier memory.

    Parameters
    ----------
    retriever : Retriever | None
        Shared Retriever (ChromaDB) instance. Created automatically if None.
    max_iterations : int
        Hard cap on think-act-observe iterations per query.
    """

    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        max_iterations: int = _MAX_ITERATIONS,
    ):
        self.llm            = LLM()
        self.retriever      = retriever or Retriever()
        self.registry       = build_registry(retriever=self.retriever)
        self.memory         = Memory(retriever=self.retriever)
        self.planner        = Planner(self.llm)
        self.max_iterations = max_iterations
        logger.info("ReActAgent ready | tools=%s", self.registry.names())

    # ── Public API ────────────────────────────────────────────────

    def run(self, query: str) -> str:
        """Run full agentic pipeline and return the final answer."""
        logger.info("Agent.run | %s", query[:120])
        _, messages = self._build_messages(query)
        answer = self._react_loop(messages)
        self.memory.snapshot(query, answer)
        return answer

    def stream(self, query: str) -> Iterator[str]:
        """Yield the final answer token-by-token; tool calls are silent."""
        logger.info("Agent.stream | %s", query[:120])
        _, messages = self._build_messages(query)
        messages    = self._tool_phase(messages)

        full_response = ""
        for chunk in self.llm.stream_response(messages):
            full_response += chunk
            yield chunk

        answer = extract_final_answer(full_response) or full_response
        self.memory.snapshot(query, answer)

    # ── Internals ─────────────────────────────────────────────────

    def _build_messages(self, query: str):
        memory_context = self.memory.recall(query) or "None"
        plan_str = self.planner.plan_str(
            query,
            self.registry.names(),
            memory_context if memory_context != "None" else "",
        )
        system_content = _AGENT_SYSTEM.format(
            tool_schemas   = self.registry.all_schemas(),
            plan           = plan_str,
            memory_context = memory_context,
        )
        messages: List[dict] = [
            {"role": "system", "content": system_content},
            *self.memory.short_term_messages(),
            {"role": "user",   "content": query},
        ]
        return system_content, messages

    def _react_loop(self, messages: List[dict]) -> str:
        for i in range(1, self.max_iterations + 1):
            logger.info("ReAct iter %d/%d", i, self.max_iterations)
            response = self.llm.generate_response(messages)
            messages.append({"role": "assistant", "content": response})

            answer = extract_final_answer(response)
            if answer:
                logger.info("✅ Final answer on iter %d", i)
                return answer

            tool_calls = parse_tool_calls(response)
            if tool_calls:
                obs = self._execute_all(tool_calls)
                messages.append({"role": "user", "content": self._fmt_obs(obs)})
                continue

            return response.strip()

        logger.warning("Max iterations reached.")
        return "Unable to complete within the allowed steps. Try a more specific query."

    def _tool_phase(self, messages: List[dict]) -> List[dict]:
        for _ in range(self.max_iterations - 1):
            response = self.llm.generate_response(messages)
            messages.append({"role": "assistant", "content": response})
            if has_final_answer(response):
                return messages
            tool_calls = parse_tool_calls(response)
            if not tool_calls:
                return messages
            obs = self._execute_all(tool_calls)
            messages.append({"role": "user", "content": self._fmt_obs(obs)})
        return messages

    def _execute_all(self, tool_calls: List[dict]) -> List[tuple]:
        results = []
        for call in tool_calls:
            name = call.get("name", "")
            args = call.get("arguments", {})
            tool = self.registry.get(name)
            if tool is None:
                result = f"Unknown tool '{name}'. Available: {self.registry.names()}"
            else:
                logger.info("→ %s(%s)", name, args)
                result = tool(**args)
                logger.info("← %s: %s…", name, str(result)[:120])
            results.append((name, result))
        return results

    @staticmethod
    def _fmt_obs(observations: List[tuple]) -> str:
        return "\n\n".join(
            f'<tool_result name="{n}">\n{r}\n</tool_result>'
            for n, r in observations
        )
