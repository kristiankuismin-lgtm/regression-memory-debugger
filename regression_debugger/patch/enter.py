"""Enter Pro patch applier (documented integration seam).

The hackathon brief frames Enter Pro as the AI-native platform you BUILD and
DEPLOY on, driven by natural language — the "speed of thought" execution layer.
This applier hands the recalled fix to an Enter environment so the patch can be
applied/deployed there.

Set ENTER_API_URL and ENTER_API_KEY to enable. Until then, use LocalPatchApplier
(the default), which writes the same proposal to disk. Verify the exact endpoint
shape against your Enter Pro project before relying on this in production.
"""

from __future__ import annotations

import json
import urllib.request

from regression_debugger.patch.base import PatchApplier
from regression_debugger.types import Diagnosis


class EnterPatchApplier(PatchApplier):
    def __init__(self, api_url: str, api_key: str, project: str = ""):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.project = project

    def propose(self, diagnosis: Diagnosis) -> str:
        m = diagnosis.match
        payload = {
            "project": self.project,
            "instruction": (
                "Apply this previously-verified fix for a recurring regression.\n"
                f"Symptom: {diagnosis.bug.symptom}\n"
                + (f"Root cause: {m.root_cause}\nFix: {m.fix}\n"
                   f"Files: {', '.join(m.files)}\n" if m else "")
            ),
            "confidence": diagnosis.confidence,
            "source_bug": m.id if m else None,
        }
        req = urllib.request.Request(
            f"{self.api_url}/v1/patches",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("url") or data.get("id") or "enter:submitted"
