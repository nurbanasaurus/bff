#!/usr/bin/env python3
"""bff: let a local-model agent (Hermes) consult Claude Code on the same box.

Claude Code's headless mode (`claude -p`) runs under the machine owner's
existing login and subscription: no API key, no third-party billing, no new
data path. bff wraps it in two calls:

    ask(prompt)                      one-shot consult, returns (text, session_id)
    ask(prompt, session_id=sid)      follow-up in the same conversation

Sessions make it a real dialogue: the local agent can push back, Claude
remembers the thread. Headless mode cannot write or run shell commands
without explicit permission flags bff never passes, so a consult can read
the machine to answer but cannot mutate it.

Stdlib only. Python 3.9+.
"""
import json
import subprocess
import shutil

DEFAULT_MODEL = "sonnet"   # consults are usually reasoning, not long-horizon work
DEFAULT_TIMEOUT = 300      # seconds; hard questions take time


class BffError(RuntimeError):
    pass


def claude_available() -> bool:
    return shutil.which("claude") is not None


def ask(prompt, session_id=None, model=DEFAULT_MODEL, system=None,
        timeout=DEFAULT_TIMEOUT, cwd=None):
    """Consult Claude Code. Returns (answer_text, session_id).

    Pass the returned session_id back in to continue the same conversation.
    `system` appends consult framing without replacing Claude Code's own
    system prompt. `cwd` sets the directory Claude reads from when the
    question is about a specific project.
    """
    if not claude_available():
        raise BffError("claude CLI not found on PATH; install Claude Code first")
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    if session_id:
        cmd += ["--resume", session_id]
    if model:
        cmd += ["--model", model]
    if system:
        cmd += ["--append-system-prompt", system]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, cwd=cwd)
    except subprocess.TimeoutExpired:
        raise BffError(f"claude timed out after {timeout}s")
    if proc.returncode != 0:
        raise BffError(f"claude exited {proc.returncode}: {proc.stderr.strip()[:500]}")
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise BffError(f"unparseable claude output: {proc.stdout[:300]}")
    if out.get("is_error"):
        raise BffError(f"claude reported an error: {str(out.get('result'))[:500]}")
    return out.get("result", ""), out.get("session_id")


CONSULT_FRAMING = (
    "You are being consulted by a local-model agent running on this same "
    "machine. It asked because the question exceeds its knowledge or "
    "reasoning depth. Answer directly and completely; say plainly when you "
    "are unsure. Do not modify anything on the machine. The conversation "
    "may continue across turns; hold your positions unless given a reason "
    "to change them."
)

PERSONA_FRAMING = (
    "Answer AS {name}, the owner's persona, whose profile and durable "
    "state were injected at session start. Use that memory: who the owner "
    "is, what is active in their life, their voice contract. You are being "
    "consulted by another agent of the same owner; share what you know "
    "about the owner freely with it, it works for the same person. If your "
    "injected state does not cover the question, say so rather than "
    "guessing."
)


def consult(prompt, session_id=None, **kw):
    """ask() with the consult framing pre-applied. Same return shape."""
    kw.setdefault("system", CONSULT_FRAMING)
    return ask(prompt, session_id=session_id, **kw)


def persona_name():
    """The persona's name from ~/.aria/profile.yaml, or None if no persona
    is set up (the aria plugin owns that file)."""
    try:
        from pathlib import Path
        for ln in (Path.home() / ".aria" / "profile.yaml").read_text().splitlines():
            if ln.startswith("name:"):
                return ln.split(":", 1)[1].strip().strip('"').strip("'") or None
    except OSError:
        pass
    return None


def ask_persona(prompt, session_id=None, **kw):
    """Consult the owner's persona (Echo, Aria, whoever the aria plugin
    grew) instead of a bare Claude. The persona's memory arrives via the
    aria plugin's SessionStart hook, which fires in headless mode too.
    Raises BffError if no persona is configured."""
    name = persona_name()
    if not name:
        raise BffError("no persona configured (~/.aria/profile.yaml missing); "
                       "run /aria-init in Claude Code or use consult() instead")
    kw.setdefault("system", CONSULT_FRAMING + " " +
                  PERSONA_FRAMING.format(name=name))
    return ask(prompt, session_id=session_id, **kw)


if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if a != "--persona"]
    use_persona = "--persona" in sys.argv
    if not args:
        print("usage: bff.py [--persona] <question> [session_id]")
        raise SystemExit(2)
    sid = args[1] if len(args) > 1 else None
    fn = ask_persona if use_persona else consult
    text, new_sid = fn(args[0], session_id=sid)
    print(text)
    print(f"\n[session: {new_sid}]")
