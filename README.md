# bff

Let a local-model agent consult Claude Code on the same machine. Two minds,
one box, the owner's own subscription.

Hermes (or any local-model agent) runs on small models. They're fast and
private and they hit a ceiling. Claude Code is already installed on the same
machine, already authenticated, already paid for. bff is the hallway between
them: when the local agent meets a question above its depth, it walks over
and asks.

No API keys. No third-party billing. `claude -p` headless mode runs under
the machine owner's existing login, so a consult is native usage, the same
as the owner typing the question themselves.

## Pieces

| File | What it is |
|---|---|
| `bff.py` | Core. `ask()` for one-shot consults, session_id resume for real multi-turn conversations. Stdlib only. Tested live. |
| `converse.py` | Moderated dialogue: local Ollama model and Claude alternate turns on a topic until they converge or hit the turn cap. Transcript written to disk. |
| `hermes_tool_bff.py` | Hermes tool adapter (`ask_claude`). Consult logic is real; the registration wrapper is an honest stub to align with the live Hermes tool contract on deploy. |

## Quick taste

```sh
python3 bff.py "What's the practical difference between rebase and merge?"
# answer, plus a session id

python3 bff.py "Which should a small team default to?" <session-id>
# Claude remembers the thread; it's a conversation, not a search box
```

Dialogue mode:

```sh
python3 converse.py "How should the backup rotation be structured?" \
  --ollama-host http://dev0x00:11434 --local-model qwen3:14b \
  --max-turns 6 --out decision.md
```

## Calling the persona

If the machine runs the [aria plugin](https://github.com/nurbanasaurus/aria-plugin),
the owner has a named persona (Echo, Aria, whoever they grew) whose memory
is injected into every Claude Code session, headless included. bff can
consult that persona instead of a bare Claude:

```sh
python3 bff.py --persona "What's on the owner's plate this week?"
# answered by the persona, from its real memory of the owner
```

From Hermes: `ask_claude(question, persona=True)`. The routing rule for the
local model: persona for questions about the owner's life, plans, and
preferences; bare consult for technical questions. Both agents work for the
same person, so the persona shares what it knows.

## Safety posture

- Consults are read-capable, write-denied. Headless Claude Code can read
  the machine to answer accurately but bff never passes the permission
  flags that would let it modify anything.
- The consult framing tells Claude it's advising another agent, to answer
  plainly, and to say when it's unsure.
- Conversations have a hard turn cap and a stop word, so two agents can't
  talk forever on the owner's plan.

## Cost honesty

Consults draw from the owner's Claude subscription limits, the same pool
as their own usage. A chatty local agent can burn real budget. The Hermes
trigger should be "above my depth," not "every message."

## Deploy to Hermes

Verified live on a real Hermes install (macOS, launchd-managed gateway).

1. Copy `bff.py` and `hermes_tool_bff.py` (deploy it as `bff_tool.py`) into
   the host's `hermes-agent/tools/`. `bff.py` is the library (no top-level
   `registry.register`, so the tool discovery ignores it); `bff_tool.py`
   self-registers `ask_claude` under toolset `bff`.
2. Enable the toolset: add `bff` to the relevant surfaces under
   `platform_toolsets` in `config.yaml` (e.g. `cli`, `api_server`). Do this
   surgically, alphabetically, and back the file up first.
3. Restart the gateway (`launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway`).
   The tool auto-discovers; `ask_claude` then appears on the enabled surfaces.

### Telling the agent it exists

A registered tool the agent never reaches for is dead weight. Add a short
instruction to the agent's operating doc (Hermes's `AGENTS.md`) pointing at
`ask_claude`: plain for technical depth, `persona=true` to consult the
owner's persona about the owner's life, and "when you just do not know, ask
rather than guess."

**AGENTS.md edits are APPEND-ONLY.** That file is hand-maintained by the
owner. Never overwrite or replace an existing section. Insert new guidance
before a stable later heading and diff against a backup to confirm the
change is insertions only, zero deletions. `echo_append.md` is the snippet
used on the reference install (appended, not substituted).
