"""PatchApplier interface — turns a recalled fix into an actionable patch."""

from __future__ import annotations

from typing import Protocol

from regression_debugger.types import Diagnosis


class PatchApplier(Protocol):
    def propose(self, diagnosis: Diagnosis) -> str:
        """Produce a patch proposal for a known regression. Returns a ref/path/url."""
        ...
