# Regression Memory Debugger

> A "sentient" debugging teammate for the Quackathon 2026 **Software** track.
> It **remembers every bug it has ever fixed** (via **Parcle** long-term memory)
> and, when a paraphrased version of that bug shows up again, **recognizes the
> recurrence and proposes the known fix** — autonomously, in the **Enter Pro**
> environment, with a heads-up in **Slack**.

**▶ Live dashboard:** https://kristiankuismin-lgtm.github.io/regression-memory-debugger/ — paste a bug and watch the agent recall the fix in your browser (same logic as the Python agent).

Most coding agents are stateless: they re-debug the same regression every time it
reappears under slightly different wording. This agent gets *smarter every time a
bug is resolved*, because the fix is written to memory and recalled on the next
occurrence — even when a different person reports it in different words.

---

## The loop

```
incoming bug  ──►  recall similar past bugs   ──►  known regression?
(PostHog/         (Parcle: "have we seen           │
 Produck/          this before?")                  ├─ yes ─► propose known fix
 Slack/webhook)                                    │         (Enter Pro) + Slack
                                                   └─ no  ─► flag as new + Slack
resolved bug  ──►  write fix to long-term memory (Parcle)   ◄── gets smarter
```

The agent is **storage-agnostic**. With no API keys it runs fully offline on a
local memory store, so the demo is deterministic. Set `PARCLE_API_KEY` and it
switches to real Parcle semantic memory — no code changes.

---

## Quickstart (zero setup, offline)

```bash
# no dependencies required for the local demo
python -m regression_debugger.cli demo
```

That runs the scripted before/after: empty memory → teach one fix → a *different*
user reports a paraphrased recurrence → the agent recalls the fix → an unrelated
bug is correctly flagged as new.

Other commands:

```bash
python -m regression_debugger.cli seed                  # load 8 resolved bugs
python -m regression_debugger.cli query "HMAC check fails on PostHog events"
python -m regression_debugger.cli list                  # inspect memory
```

## Run the autonomous webhook (closed loop)

```bash
pip install -r requirements.txt
python -m regression_debugger.cli seed
uvicorn regression_debugger.server:app --reload

curl -X POST localhost:8000/webhook/bug \
  -H 'content-type: application/json' \
  -d '{"title":"dupes","symptom":"same company shows up many times in results"}'
```

## Turn on the real stack

Copy `.env.example` to `.env` and fill in what you have:

| Variable | Effect |
|---|---|
| `PARCLE_API_KEY` | Use Parcle long-term memory instead of the local store |
| `ENTER_API_URL` / `ENTER_API_KEY` | Apply/deploy the patch in Enter Pro instead of writing a local file |
| `SLACK_WEBHOOK_URL` | Post verdicts to Slack instead of the console preview |

See [`INTEGRATION.md`](INTEGRATION.md) for exactly how Parcle and Enter Pro are wired.

---

## Architecture

```
regression_debugger/
├── types.py            BugReport, MemoryEntry, Diagnosis
├── similarity.py       offline TF-IDF + cosine (+ synonym fold) for local recall
├── memory/
│   ├── base.py         MemoryStore protocol + SearchResult
│   ├── local.py        offline JSON store (default)
│   └── parcle_store.py Parcle-backed store (official SDK)
├── patch/
│   ├── local.py        writes a Markdown patch proposal (default)
│   └── enter.py        hands the fix to Enter Pro
├── notify/slack.py     Slack Block Kit message (console fallback)
├── agent.py            learn() / diagnose() orchestration
├── config.py           env-driven backend wiring
├── cli.py              seed / query / list / demo
└── server.py           FastAPI webhook — the autonomous loop
```

Key design choice: a single confidence threshold (`KNOWN_THRESHOLD`, default
`0.25`) decides "known regression" vs "new bug", and the same `MemoryStore`
interface backs both the offline and Parcle modes. The local backend matches on
shared vocabulary; Parcle matches semantically, so it catches paraphrases the
local store would miss.

## Tests

```bash
pip install pytest && python -m pytest -q
```

Covers tokenization, cosine, paraphrase recall, and correct novelty detection.

---

## Submission checklist (Quackathon Track 01)

- **GitHub repo + README** — this repository.
- **Demo video script** — [`DEMO.md`](DEMO.md) (≤ 2 min walkthrough).
- **Live project** — `uvicorn regression_debugger.server:app` (deployable on Enter Pro).
- **Tool integration** — [`INTEGRATION.md`](INTEGRATION.md): Parcle (memory) + Enter Pro (execution) + Slack.

## License

MIT
