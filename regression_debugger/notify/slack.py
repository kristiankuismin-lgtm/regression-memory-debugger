"""Slack notifier — posts the agent's verdict to a channel.

Uses a Slack incoming webhook (SLACK_WEBHOOK_URL). Falls back to printing a
formatted block to stdout when no webhook is configured, so the demo always
shows the message the team would receive.
"""

from __future__ import annotations

import json
import urllib.request

from regression_debugger.types import Diagnosis


class SlackNotifier:
    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url

    def _blocks(self, d: Diagnosis) -> dict:
        if d.is_known:
            header = f":repeat: Known regression ({d.confidence:.0%} match)"
        else:
            header = ":sparkles: New bug — no prior match in memory"
        lines = [header, "", f"*Bug:* {d.bug.title or d.bug.symptom[:80]}", d.answer]
        if d.suggested_patch:
            lines.append(f"\n*Suggested patch:* {d.suggested_patch}")
        text = "\n".join(lines)
        return {
            "text": header,
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": text}},
            ],
        }

    def send(self, d: Diagnosis) -> None:
        payload = self._blocks(d)
        if not self.webhook_url:
            print("\n--- SLACK (preview, no webhook configured) ---")
            print(payload["blocks"][0]["text"]["text"])
            print("--- end Slack preview ---\n")
            return
        req = urllib.request.Request(
            self.webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=15)  # noqa: S310
