"""RegressionAgent — the orchestration layer.

learn()    : teach the agent a resolved bug (writes to long-term memory).
diagnose() : given a new bug, recall similar past regressions, decide whether
             it's a known regression, propose a patch, and notify Slack.

This is the "sentient engineer" loop: it gets smarter every time a bug is
resolved, because the fix is remembered and recalled on the next occurrence.
"""

from __future__ import annotations

from regression_debugger.memory.base import MemoryStore
from regression_debugger.notify.slack import SlackNotifier
from regression_debugger.patch.base import PatchApplier
from regression_debugger.types import BugReport, Diagnosis, MemoryEntry


class RegressionAgent:
    def __init__(
        self,
        memory: MemoryStore,
        patcher: PatchApplier | None = None,
        notifier: SlackNotifier | None = None,
        known_threshold: float = 0.25,
    ):
        self.memory = memory
        self.patcher = patcher
        self.notifier = notifier
        self.known_threshold = known_threshold

    def learn(self, entry: MemoryEntry) -> None:
        self.memory.record(entry)

    def diagnose(self, bug: BugReport, *, notify: bool = True,
                 propose_patch: bool = True) -> Diagnosis:
        result = self.memory.search(bug.text())
        is_known = result.confidence >= self.known_threshold

        if is_known:
            answer = "Seen before. " + result.answer
        elif result.match is not None:
            answer = (
                f"No known regression above the {self.known_threshold:.0%} confidence bar "
                f"(closest: '{result.match.title}' at {result.confidence:.0%}). "
                f"Treating as a new bug."
            )
        else:
            answer = result.answer

        diagnosis = Diagnosis(
            status="known_regression" if is_known else "novel",
            confidence=result.confidence,
            answer=answer,
            bug=bug,
            match=result.match if is_known else None,
            citations=result.citations if is_known else [],
        )

        if is_known and propose_patch and self.patcher is not None:
            diagnosis.suggested_patch = self.patcher.propose(diagnosis)

        if notify and self.notifier is not None:
            self.notifier.send(diagnosis)

        return diagnosis
