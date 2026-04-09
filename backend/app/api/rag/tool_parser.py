"""
tool_parser.py
──────────────
Parse <tool_call>…</tool_call> and <final_answer>…</final_answer> blocks
from raw LLM output.  Uses json-repair as a fallback so truncated or
slightly malformed JSON still gets parsed (same approach as the project-builder
and llm-tools notebooks).
"""

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from json_repair import repair_json
    _HAS_REPAIR = True
except ImportError:
    _HAS_REPAIR = False
    logger.warning("json-repair not installed; malformed tool-call JSON will be dropped.")

# Compiled once at import time
_TOOL_CALL_RE    = re.compile(r"<tool_call>(.*?)</tool_call>",       re.DOTALL)
_FINAL_ANSWER_RE = re.compile(r"<final_answer>(.*?)</final_answer>", re.DOTALL)


# ── public API ────────────────────────────────────────────────────────────────

def parse_tool_calls(text: str) -> list[dict]:
    """
    Return a list of parsed tool-call dicts found in *text*.

    Each dict has the shape::

        {"name": "tool_name", "arguments": {"param": "value", ...}}

    Malformed JSON blocks are repaired with json-repair when available,
    and silently dropped otherwise.
    """
    calls = []
    for match in _TOOL_CALL_RE.finditer(text):
        raw = match.group(1).strip()
        parsed = _safe_parse(raw)
        if parsed is not None:
            calls.append(parsed)
    return calls


def extract_final_answer(text: str) -> Optional[str]:
    """
    Return the content inside the first <final_answer> block, or None.
    """
    match = _FINAL_ANSWER_RE.search(text)
    if match:
        return match.group(1).strip()
    return None


def has_tool_calls(text: str) -> bool:
    return bool(_TOOL_CALL_RE.search(text))


def has_final_answer(text: str) -> bool:
    return bool(_FINAL_ANSWER_RE.search(text))


# ── internal ──────────────────────────────────────────────────────────────────

def _safe_parse(raw: str) -> Optional[dict]:
    # Fast path: valid JSON
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Repair path
    if _HAS_REPAIR:
        try:
            repaired = repair_json(raw)
            result = json.loads(repaired)
            logger.debug("Repaired tool-call JSON: %s", raw[:120])
            return result
        except Exception:
            pass

    logger.warning("Could not parse tool-call JSON (dropped): %s", raw[:200])
    return None
