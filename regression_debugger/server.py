"""Webhook server — the autonomous closed loop.

POST /webhook/bug  with a bug payload (mirrors a PostHog / Produck / Slack
feedback event). The agent recalls memory, decides if it's a known regression,
proposes a patch, and notifies Slack — all without a human in the loop.

Run:
    pip install -r requirements.txt
    uvicorn regression_debugger.server:app --reload

Try:
    curl -X POST localhost:8000/webhook/bug \\
         -H 'content-type: application/json' \\
         -d '{"title":"dupes","symptom":"same company shows up many times"}'
"""

from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("Install server deps: pip install -r requirements.txt") from exc

from regression_debugger.config import backend_summary, build_agent
from regression_debugger.types import BugReport

app = FastAPI(title="Regression Memory Debugger")
_agent = build_agent()


class BugPayload(BaseModel):
    symptom: str
    title: str = ""
    source: str = "webhook"
    metadata: dict[str, Any] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "backends": backend_summary()}


@app.post("/webhook/bug")
def webhook_bug(payload: BugPayload) -> dict[str, Any]:
    bug = BugReport(
        symptom=payload.symptom,
        title=payload.title,
        source=payload.source,
        metadata=payload.metadata,
    )
    d = _agent.diagnose(bug)
    return {
        "status": d.status,
        "confidence": d.confidence,
        "answer": d.answer,
        "suggested_patch": d.suggested_patch,
        "citations": [c.__dict__ for c in d.citations],
    }
