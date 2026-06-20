"""Parcle-backed long-term memory.

Uses the official Parcle SDK (`pip install parcle`). Activated when
PARCLE_API_KEY is set (see config.py). The SDK is imported lazily so the
offline LocalMemoryStore never requires the package to be installed.

Parcle API surface (from the official quickstart):
    client = Parcle(api_key="pk_live_...")        # or PARCLE_API_KEY env
    client.ingest_dialog(user_id=..., messages=[{"role","content"}], session_id=?)
    result = client.search(user_id=..., query=...)
    result.answer / result.confidence / result.citations

We store each resolved bug as a short structured dialog scoped to a team
`user_id` (e.g. one memory namespace per repo / team), then recall it with a
natural-language question on each new bug.
"""

from __future__ import annotations

from regression_debugger.memory.base import MemoryStore, SearchResult
from regression_debugger.types import Citation, MemoryEntry


class ParcleMemoryStore(MemoryStore):
    def __init__(self, namespace: str = "regression-debugger", threshold: float = 0.55,
                 api_key: str | None = None):
        try:
            from parcle import Parcle  # lazy import
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "Parcle SDK not installed. Run `pip install parcle`, or unset "
                "PARCLE_API_KEY to use the offline local store."
            ) from exc

        # Reads PARCLE_API_KEY from the environment when api_key is None.
        self._client = Parcle(api_key=api_key) if api_key else Parcle()
        self._namespace = namespace
        self.threshold = threshold
        # Local mirror so all()/demos can list what we've taught it this run.
        self._mirror: list[MemoryEntry] = []

    def record(self, entry: MemoryEntry) -> None:
        # Encode the resolved bug as a compact dialog turn. Parcle synthesizes
        # over this when we later ask "have we seen this before?".
        content = (
            f"RESOLVED BUG [{entry.id}] {entry.title}\n"
            f"Symptom: {entry.symptom}\n"
            f"Root cause: {entry.root_cause}\n"
            f"Fix: {entry.fix}\n"
            f"Files: {', '.join(entry.files) or 'n/a'}\n"
            f"Tags: {', '.join(entry.tags) or 'n/a'}"
        )
        self._client.ingest_dialog(
            user_id=self._namespace,
            messages=[
                {"role": "user", "content": f"We hit a bug: {entry.symptom}"},
                {"role": "assistant", "content": content},
            ],
        )
        self._mirror = [e for e in self._mirror if e.id != entry.id] + [entry]

    def all(self) -> list[MemoryEntry]:
        return list(self._mirror)

    def search(self, query: str) -> SearchResult:
        result = self._client.search(
            user_id=self._namespace,
            query=(
                f"Have we seen this bug before? If so, what was the root cause "
                f"and the fix that worked? Bug: {query}"
            ),
        )
        confidence = float(getattr(result, "confidence", 0.0) or 0.0)
        answer = getattr(result, "answer", "") or ""
        citations = [
            Citation(type=getattr(c, "type", "session"), id=str(getattr(c, "id", "")))
            for c in (getattr(result, "citations", []) or [])
        ]
        # Try to resolve the cited bug back to our mirror for patch suggestions.
        match = None
        cited_ids = {c.id for c in citations}
        for entry in self._mirror:
            if entry.id in cited_ids or entry.id in answer:
                match = entry
                break
        return SearchResult(answer=answer, confidence=confidence,
                            match=match, citations=citations)
