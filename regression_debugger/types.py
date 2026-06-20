"""Core data types for the Regression Memory Debugger."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class BugReport:
    """An incoming bug, e.g. from PostHog, Slack, or a Produck feedback event."""

    symptom: str
    title: str = ""
    source: str = "manual"  # posthog | slack | produck | manual | webhook
    metadata: dict[str, Any] = field(default_factory=dict)

    def text(self) -> str:
        """The text used for similarity search."""
        return f"{self.title}\n{self.symptom}".strip()


@dataclass
class MemoryEntry:
    """A resolved bug stored in long-term memory (a regression we can recall)."""

    id: str
    title: str
    symptom: str
    root_cause: str
    fix: str
    files: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)

    def text(self) -> str:
        return f"{self.title}\n{self.symptom}\n{self.root_cause}".strip()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MemoryEntry":
        return cls(**d)


@dataclass
class Citation:
    type: str  # "bug" | "session" | "file"
    id: str
    detail: str = ""


@dataclass
class Diagnosis:
    """The agent's verdict on an incoming bug."""

    status: str  # "known_regression" | "novel"
    confidence: float
    answer: str
    bug: BugReport
    match: MemoryEntry | None = None
    citations: list[Citation] = field(default_factory=list)
    suggested_patch: str | None = None

    @property
    def is_known(self) -> bool:
        return self.status == "known_regression"
