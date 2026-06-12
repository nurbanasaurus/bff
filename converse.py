#!/usr/bin/env python3
"""bff converse: a moderated dialogue between a local Ollama model and Claude.

Two minds, one problem. The local model opens, Claude responds, they
alternate until one of them says the agreed stop word or the turn cap
hits. The full transcript is written to disk so the human can audit what
their machines decided together.

Usage:
    python3 converse.py "How should we structure the backup rotation?" \
        --ollama-host http://localhost:11434 --local-model qwen3:14b \
        --max-turns 6 --out transcript.md

Stdlib only.
"""
import argparse
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import bff

STOP_WORD = "AGREED."

LOCAL_SYSTEM = (
    "You are the local model in a two-agent working session on one machine. "
    "Your counterpart is Claude, a stronger general model. State your view, "
    "challenge weak reasoning, concede when convinced. When you and Claude "
    f"have converged on an answer, end your message with the single word "
    f"{STOP_WORD}"
)

CLAUDE_SYSTEM = (
    bff.CONSULT_FRAMING + " You are in a working dialogue with the local "
    "model. Engage its arguments specifically; do not just restate your "
    f"position. When you have genuinely converged, end with {STOP_WORD}"
)


def ollama_chat(host, model, messages, timeout=300):
    body = json.dumps({"model": model, "messages": messages,
                       "stream": False}).encode()
    req = urllib.request.Request(f"{host.rstrip('/')}/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        out = json.loads(resp.read())
    return out["message"]["content"]


def converse(topic, ollama_host, local_model, max_turns=6, out_path=None,
             claude_model=bff.DEFAULT_MODEL):
    transcript = [f"# bff converse: {topic}",
                  f"Started {datetime.now(timezone.utc).isoformat()}",
                  f"Local: {local_model} | Claude: {claude_model}", ""]
    local_msgs = [{"role": "system", "content": LOCAL_SYSTEM},
                  {"role": "user", "content": f"Topic: {topic}\nOpen the discussion with your initial take."}]
    session_id = None
    for turn in range(1, max_turns + 1):
        local_say = ollama_chat(ollama_host, local_model, local_msgs)
        transcript += [f"## Turn {turn}: {local_model}", local_say, ""]
        local_msgs.append({"role": "assistant", "content": local_say})
        if STOP_WORD in local_say:
            break
        claude_prompt = (f"Topic under discussion: {topic}\n\n"
                         f"The local model says:\n{local_say}\n\nYour response:")
        claude_say, session_id = bff.ask(claude_prompt, session_id=session_id,
                                         model=claude_model, system=CLAUDE_SYSTEM)
        transcript += [f"## Turn {turn}: claude", claude_say, ""]
        local_msgs.append({"role": "user", "content": f"Claude responds:\n{claude_say}"})
        if STOP_WORD in claude_say:
            break
    text = "\n".join(transcript)
    if out_path:
        Path(out_path).write_text(text)
    return text


def main():
    ap = argparse.ArgumentParser(description="dialogue between local model and Claude")
    ap.add_argument("topic")
    ap.add_argument("--ollama-host", default="http://localhost:11434")
    ap.add_argument("--local-model", default="qwen3:14b")
    ap.add_argument("--claude-model", default=bff.DEFAULT_MODEL)
    ap.add_argument("--max-turns", type=int, default=6)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    print(converse(args.topic, args.ollama_host, args.local_model,
                   max_turns=args.max_turns, out_path=args.out,
                   claude_model=args.claude_model))


if __name__ == "__main__":
    main()
