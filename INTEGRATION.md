# Tool Integration

How the three hackathon tools are used. The agent runs without any of them
(offline fallbacks), and each one is enabled by setting its env var(s).

## Parcle — long-term memory (the core of the project)

Parcle is the agent's persistent memory: it remembers every resolved bug and
recalls the matching fix when a recurrence appears.

- **SDK:** official `parcle` package (`pip install parcle`), key format `pk_live_…`,
  read from `PARCLE_API_KEY`.
- **Write (on fix):** each resolved bug is stored with `client.ingest_dialog(...)`,
  scoped to a team `user_id` namespace (`PARCLE_NAMESPACE`). Symptom, root cause,
  fix, and touched files are encoded into the dialog turn.
- **Read (on new bug):** `client.search(user_id=..., query="have we seen this
  bug before? what was the fix?")` returns a synthesized `answer`, a `confidence`
  score, and `citations` back to the original bug sessions.
- **Why it matters:** Parcle's "ask, don't query" search is what lets the agent
  recognize a *paraphrased* recurrence — different words, same underlying bug —
  which a plain keyword search misses.

Code: `regression_debugger/memory/parcle_store.py`.
Offline fallback: `regression_debugger/memory/local.py` (TF-IDF cosine + synonym fold).

## Enter Pro — execution / deployment layer

Enter Pro is the AI-native platform the agent is built to run and deploy on, and
the target for applying the recalled fix.

- The webhook service (`server.py`) is the deployable unit you run on Enter Pro.
- When a known regression is confirmed, `EnterPatchApplier` hands the verified
  fix to the Enter environment as a natural-language patch instruction
  (`ENTER_API_URL`, `ENTER_API_KEY`, `ENTER_PROJECT`).
- **Verify the endpoint shape against your Enter Pro project before relying on
  it in production.** Until configured, `LocalPatchApplier` writes the identical
  proposal to `out/patches/*.patch.md` so the loop is fully demoable.

Code: `regression_debugger/patch/enter.py`.

## Slack — team notification

Each verdict (known regression with proposed fix, or a new bug) is posted to
Slack via an incoming webhook (`SLACK_WEBHOOK_URL`). Without a webhook, the same
message is printed as a console preview.

Code: `regression_debugger/notify/slack.py`.

## Optional incoming sources

The webhook payload mirrors a PostHog / Produck / Slack feedback event, so any of
those can POST bugs to `/webhook/bug` to drive the loop automatically.
