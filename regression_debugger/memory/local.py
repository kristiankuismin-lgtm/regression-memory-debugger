"""Offline, deterministic memory store.

Persists entries to a JSON file and recalls them with TF-IDF cosine similarity.
Mirrors Parcle's "synthesized answer + confidence + citations" response shape so
the rest of the app doesn't care which backend is active.
"""

from __future__ import annotations

import json
from pathlib import Path

from regression_debugger.memory.base import MemoryStore, SearchResult
from regression_debugger.similarity import build_idf, cosine, tfidf_vector, tokenize
from regression_debugger.types import Citation, MemoryEntry


class LocalMemoryStore(MemoryStore):
    def __init__(self, path: str | Path, threshold: float = 0.30):
        self.path = Path(path)
        self.threshold = threshold
        self._entries: list[MemoryEntry] = []
        self._load()

    # --- persistence -----------------------------------------------------
    def _load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._entries = [MemoryEntry.from_dict(d) for d in raw]

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([e.to_dict() for e in self._entries], indent=2),
            encoding="utf-8",
        )

    # --- MemoryStore -----------------------------------------------------
    def record(self, entry: MemoryEntry) -> None:
        self._entries = [e for e in self._entries if e.id != entry.id]
        self._entries.append(entry)
        self._save()

    def all(self) -> list[MemoryEntry]:
        return list(self._entries)

    def search(self, query: str) -> SearchResult:
        if not self._entries:
            return SearchResult(answer="No prior bugs in memory yet.", confidence=0.0)

        corpus = [tokenize(e.text()) for e in self._entries]
        idf = build_idf(corpus + [tokenize(query)])
        qv = tfidf_vector(tokenize(query), idf)

        best_entry: MemoryEntry | None = None
        best_score = 0.0
        for entry, toks in zip(self._entries, corpus):
            score = cosine(qv, tfidf_vector(toks, idf))
            if score > best_score:
                best_score, best_entry = score, entry

        if best_entry is None:
            return SearchResult(answer="No similar past bug found.", confidence=0.0)

        # Always return the closest prior bug with its score; the agent applies
        # the confidence threshold to decide "known regression" vs "new bug".
        answer = (
            f"Closest prior bug: '{best_entry.title}' "
            f"(logged {best_entry.created_at[:10]}).\n"
            f"Root cause: {best_entry.root_cause}\n"
            f"Fix that worked: {best_entry.fix}"
        )
        return SearchResult(
            answer=answer,
            confidence=round(best_score, 3),
            match=best_entry,
            citations=[Citation(type="bug", id=best_entry.id, detail=best_entry.title)],
        )
