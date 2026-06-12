#!/usr/bin/env python3
"""Hermes tool adapter for bff. DEPLOY TARGET: the Hermes host's
hermes-agent/tools/ directory, alongside the existing tools.

HONEST STUB NOTICE: this file was written without access to the Hermes
tool contract (Hermes lives on a different machine). The CONSULT LOGIC
below is real and tested; the registration wrapper at the bottom is a
guess that must be aligned with an existing tool (e.g.
session_search_tool.py) before it will load. Bring one real tool file
to a Claude Code session and the wrapper rewrite takes minutes.

Intended Hermes-side behavior once wired:
- Tool name: ask_claude
- Trigger: the local model decides the question exceeds its depth, or the
  user says "ask claude" / "run it past claude".
- Multi-turn: pass the prior session_id to continue a conversation.
- The consult is read-only on the machine; Claude answers, never mutates.
"""
import sys
from pathlib import Path

# bff.py is expected next to this file after deploy; adjust if Hermes
# keeps shared libs elsewhere.
sys.path.insert(0, str(Path(__file__).parent))
import bff  # noqa: E402


def ask_claude(question: str, session_id: str = None,
               project_dir: str = None, persona: bool = False) -> dict:
    """Consult Claude Code on this machine. Returns answer + session_id.

    Args:
        question: what the local model wants Claude's take on. Include the
            context Claude can't see (conversation summary, what was tried).
        session_id: pass the session_id from a previous answer to continue
            that same conversation instead of starting fresh.
        project_dir: optional path; set it when the question is about a
            specific repo so Claude reads the right code.
        persona: True to consult the owner's persona (Echo, etc., from the
            aria plugin) with its memory of the owner, instead of a bare
            Claude. Use for questions about the owner's life, plans, or
            preferences; use False for technical questions.
    """
    try:
        fn = bff.ask_persona if persona else bff.consult
        text, sid = fn(question, session_id=session_id, cwd=project_dir)
        return {"ok": True, "answer": text, "session_id": sid}
    except bff.BffError as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# REGISTRATION WRAPPER: align with the real Hermes tool contract before use.
# Pattern this on session_search_tool.py from the live install.
# ---------------------------------------------------------------------------
TOOL_SPEC = {
    "name": "ask_claude",
    "description": (
        "Consult Claude Code running on this same machine, on the owner's "
        "own subscription. Use when a question exceeds local-model depth: "
        "hard debugging, architecture tradeoffs, unfamiliar domains, or "
        "when the user says to run something past Claude. Returns the "
        "answer and a session_id; pass the session_id back to continue the "
        "same conversation across turns."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "session_id": {"type": "string"},
            "project_dir": {"type": "string"},
            "persona": {"type": "boolean"},
        },
        "required": ["question"],
    },
    "entrypoint": ask_claude,
}
