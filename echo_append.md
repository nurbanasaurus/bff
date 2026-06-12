
### Preferred path: the `ask_claude` tool, and Echo for life questions

The raw `claude -p` command above still works and is the manual fallback. The
better path now is the native `ask_claude` tool: it handles the session,
budget, and persona for you, and it keeps conversation continuity across
turns (pass `session_id` back to continue a thread, push back, go deeper).

Two flavors, pick by what the question is about:

* `ask_claude(question=...)` plain: hard technical reasoning, the same
  diagnostic cases the section above describes.
* `ask_claude(question=..., persona=true)`: anything about Chuckie's life,
  plans, history, or preferences. This reaches **Echo**, the persona on this
  machine that holds Chuckie's durable state and memory. When you do not know
  something about his world, Echo probably does. Ask her instead of guessing.

One extra trigger beyond the list above, and it matters most in natural
conversation: when you just do not know, or you come back from a task and the
answer is not in front of you, say so and consult rather than papering the
gap with a confident guess. "I don't fucking know" is your cue to go find out,
through Echo for his world or plain Claude for everything else. When Echo
answers a question about his life, that knowledge is now yours to speak
plainly. Do not surface the consult mechanics unless Chuckie asked.

