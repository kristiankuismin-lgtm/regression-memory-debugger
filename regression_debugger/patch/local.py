"""Local patch applier — writes a Markdown patch proposal to disk.

Default applier so the closed loop is fully demoable without external systems.
"""

from __future__ import annotations

from pathlib import Path

from regression_debugger.patch.base import PatchApplier
from regression_debugger.types import Diagnosis


class LocalPatchApplier(PatchApplier):
    def __init__(self, out_dir: str | Path = "out/patches"):
        self.out_dir = Path(out_dir)

    def propose(self, diagnosis: Diagnosis) -> str:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        m = diagnosis.match
        body = [
            f"# Proposed patch for: {diagnosis.bug.title or diagnosis.bug.symptom[:60]}",
            "",
            f"**Confidence this is a known regression:** {diagnosis.confidence:.0%}",
            "",
            "## Why",
            diagnosis.answer,
            "",
        ]
        if m:
            body += [
                "## Apply the known fix",
                f"- **Root cause:** {m.root_cause}",
                f"- **Fix:** {m.fix}",
                f"- **Touch files:** {', '.join(m.files) or 'see fix notes'}",
                f"- **Source bug:** `{m.id}` ({m.created_at[:10]})",
            ]
        ref = f"bug_{(m.id if m else 'novel')}"
        path = self.out_dir / f"{ref}.patch.md"
        path.write_text("\n".join(body), encoding="utf-8")
        return str(path)
