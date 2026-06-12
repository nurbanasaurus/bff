#!/usr/bin/env python3
"""bff_tool: Hermes tool that consults Claude Code on the same machine.

Written against the live hermes-agent tool contract (tools/registry.py,
self-registration at module import). Deploy as
hermes-agent/tools/bff_tool.py with bff.py alongside it.

Two minds, one box: when a question exceeds local-model depth, Hermes
asks Claude Code through its headless mode, on the owner's own
subscription. With the aria plugin installed, persona=true consults the
owner's named persona (Echo, Aria, ...) with its memory of the owner.
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bff  # noqa: E402

from tools.registry import registry  # noqa: E402

ASK_CLAUDE_SCHEMA = {
    "name": "ask_claude",
    "description": (
        "Consult Claude Code running on this same machine, on the owner's "
        "own subscription (no API key, no third-party). Use when a question "
        "exceeds your depth: hard debugging, architecture tradeoffs, "
        "unfamiliar domains, or when the user says to run something past "
        "Claude. Returns the answer plus a session_id; pass session_id back "
        "on follow-ups to continue the same conversation. Set persona=true "
        "for questions about the owner's life, plans, or preferences: the "
        "owner's named persona answers from its memory. Use persona=false "
        "(default) for technical questions. Consults are read-only on the "
        "machine. Include context Claude cannot see (what was tried, "
        "conversation summary) in the question itself."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question, with any context Claude can't see.",
            },
            "session_id": {
                "type": "string",
                "description": "Session ID from a prior answer, to continue that conversation.",
            },
            "project_dir": {
                "type": "string",
                "description": "Absolute path; set when asking about a specific repo.",
            },
            "persona": {
                "type": "boolean",
                "description": "True to ask the owner's persona (life/plans/preferences); false for technical questions.",
            },
        },
        "required": ["question"],
    },
}


def _ask_claude(args: dict, **kw) -> str:
    question = args.get("question", "").strip()
    if not question:
        return json.dumps({"ok": False, "error": "question is required"})
    try:
        fn = bff.ask_persona if args.get("persona") else bff.consult
        text, sid = fn(question,
                       session_id=args.get("session_id") or None,
                       cwd=args.get("project_dir") or None)
        return json.dumps({"ok": True, "answer": text, "session_id": sid})
    except bff.BffError as e:
        return json.dumps({"ok": False, "error": str(e)})


def check_bff_requirements() -> bool:
    """Available only when the claude CLI is actually on this machine."""
    return bff.claude_available() or shutil.which(
        "claude", path=str(Path.home() / ".local" / "bin")) is not None


registry.register(
    name="ask_claude",
    toolset="bff",
    schema=ASK_CLAUDE_SCHEMA,
    handler=_ask_claude,
    check_fn=check_bff_requirements,
    description="Consult Claude Code (or the owner's persona) on this machine",
    emoji="🤝",
)
