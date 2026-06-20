"""Tiny, dependency-free text similarity (TF-IDF + cosine).

This powers the offline LocalMemoryStore so the demo runs deterministically
without any network or API key. When PARCLE_API_KEY is set, the Parcle adapter
takes over and this module is unused.
"""

from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Small stopword list — enough to stop generic words from dominating scores.
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "for", "and", "or", "but", "if", "then",
    "this", "that", "these", "those", "it", "its", "with", "as", "by", "from",
    "we", "i", "you", "they", "he", "she", "not", "no", "so", "do", "does",
    "did", "has", "have", "had", "can", "will", "would", "should", "when",
    "after", "before", "into", "out", "up", "down", "our", "their",
}


# Small synonym map so paraphrased bug reports (different words, same meaning)
# still recall the right prior fix. Members are folded to the canonical token.
# This is lexical query-expansion; the Parcle backend does this semantically.
_SYNONYMS_RAW = {
    "company": ["company", "companie", "firm", "vendor", "supplier", "business",
                "org", "organization", "contractor", "entity", "account"],
    "duplicate": ["duplicate", "duplicated", "dupe", "dup", "redundant", "repeated",
                  "repeating", "cloned"],
    "multiple": ["multiple", "many", "several", "times", "repeatedly", "twice"],
    "result": ["result", "listing", "entry", "entrie", "row", "record", "hit"],
    "error": ["error", "fail", "failure", "failing", "broken", "crash", "exception"],
    "stale": ["stale", "outdated", "old", "cached", "expired"],
}
_SYNONYM_MAP: dict[str, str] = {}
for _canon, _members in _SYNONYMS_RAW.items():
    for _m in _members:
        _SYNONYM_MAP[_m] = _canon


def tokenize(text: str) -> list[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    out = []
    for t in tokens:
        if t in _STOPWORDS or len(t) <= 1:
            continue
        # light stemming: drop a single trailing plural "s"
        if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        # fold synonyms to a canonical token
        t = _SYNONYM_MAP.get(t, t)
        out.append(t)
    return out


def _tf(tokens: list[str]) -> dict[str, float]:
    counts = Counter(tokens)
    total = sum(counts.values()) or 1
    return {tok: c / total for tok, c in counts.items()}


def build_idf(corpus_tokens: list[list[str]]) -> dict[str, float]:
    n_docs = len(corpus_tokens) or 1
    df: Counter[str] = Counter()
    for toks in corpus_tokens:
        for tok in set(toks):
            df[tok] += 1
    return {tok: math.log((1 + n_docs) / (1 + d)) + 1.0 for tok, d in df.items()}


def tfidf_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    tf = _tf(tokens)
    return {tok: weight * idf.get(tok, math.log(2.0) + 1.0) for tok, weight in tf.items()}


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
