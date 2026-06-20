"""MemoryStore interface.

Two implementations:
- LocalMemoryStore  : offline, deterministic, zero-dependency (default for demos).
- ParcleMemoryStore : backed by Parcle long-term memory (official SDK).

Both return the same SearchResult shape so the agent is storage-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from regression_debugger.types import Citation, MemoryEntry


@dataclass
class SearchResult:
    answer: str
    confidence: float
    match: MemoryEntry | None = None
    citations: list[Citation] = field(default_factory=list)


class MemoryStore(Protocol):
    def record(self, entry: MemoryEntry) -> None:
        """Persist a resolved bug into long-term memory."""
        ...

    def search(self, query: str) -> SearchResult:
        """Look up the most similar past regression for an incoming symptom."""
        ...

    def all(self) -> list[MemoryEntry]:
        """Return everything currently in memory (for inspection / demos)."""
        ...
