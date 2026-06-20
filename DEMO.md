# Demo video script (~2 minutes)

Goal: show the one thing only a memory-backed agent can do — recognize a
recurring bug it was taught earlier, even when a different person describes it
in different words.

**0:00 – 0:20 — The problem**
"Coding agents are stateless. They re-debug the same regression every time it
comes back under different wording. This agent remembers its fixes in Parcle and
recalls them automatically."

**0:20 – 0:35 — Empty memory**
Run `python -m regression_debugger.cli demo`.
Show step 1: a duplicate-companies bug comes in, memory is empty → flagged NEW.

**0:35 – 0:55 — Teach it once**
The team ships a fix; the agent records it to long-term memory.
"That's the only time a human is in the loop."

**0:55 – 1:30 — The payoff (the hero moment)**
Step 2: weeks later a *different* user reports what looks like a new bug —
different words ("same firm appears multiple times" vs "duplicate companies").
The agent returns: KNOWN REGRESSION, recalls the exact root cause and fix,
proposes the patch, and posts to Slack. Pause on this screen.
"It recognized a paraphrased recurrence and recalled the fix — only possible
because it remembered."

**1:30 – 1:45 — It's not just matching everything**
Step 3: an unrelated bug is correctly flagged NEW. No false positive.

**1:45 – 2:00 — The closed loop + tools**
Show the webhook: `curl` a bug to `/webhook/bug`, get the verdict back as JSON.
"Parcle is the memory, Enter Pro applies the fix, Slack tells the team. Flip one
env var to go from this offline demo to the full live stack."

## Recording tips
- Seed memory **before** recording (`cli seed`) — never live-seed on camera.
- Use a terminal with a dark theme; the verdicts are colored.
- The `demo` command pauses for [enter] between steps when run interactively.
