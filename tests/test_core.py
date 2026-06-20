"""Tests for similarity scoring and local recall behavior."""

import tempfile
from pathlib import Path

from regression_debugger.agent import RegressionAgent
from regression_debugger.memory.local import LocalMemoryStore
from regression_debugger.similarity import cosine, tfidf_vector, build_idf, tokenize
from regression_debugger.types import BugReport, MemoryEntry


def test_tokenize_drops_stopwords():
    toks = tokenize("The search returns the same company several times")
    assert "the" not in toks
    assert "search" in toks
    assert "company" in toks


def test_cosine_self_is_one():
    idf = build_idf([tokenize("duplicate company search results")])
    v = tfidf_vector(tokenize("duplicate company search results"), idf)
    assert abs(cosine(v, v) - 1.0) < 1e-9


def _agent():
    tmp = Path(tempfile.mkdtemp()) / "mem.json"
    return RegressionAgent(memory=LocalMemoryStore(tmp))


def test_recalls_paraphrased_bug():
    agent = _agent()
    agent.learn(MemoryEntry(
        id="BUG-1",
        title="Duplicate companies in search results",
        symptom="Search returns the same company several times with different names.",
        root_cause="Dedup key used name only.",
        fix="Use canonical domain + registry id.",
    ))
    d = agent.diagnose(
        BugReport(symptom="One firm shows up many times under near-identical names",
                  title="Same firm listed repeatedly"),
        notify=False,
    )
    assert d.is_known
    assert d.match is not None and d.match.id == "BUG-1"
    assert d.confidence >= 0.25


def test_unrelated_bug_is_novel():
    agent = _agent()
    agent.learn(MemoryEntry(
        id="BUG-1",
        title="Duplicate companies in search results",
        symptom="Search returns the same company several times.",
        root_cause="Dedup key used name only.",
        fix="Use canonical domain + registry id.",
    ))
    d = agent.diagnose(
        BugReport(symptom="The OAuth login button does nothing on Safari",
                  title="Login broken on Safari"),
        notify=False,
    )
    assert d.status == "novel"


def test_empty_memory_is_novel():
    agent = _agent()
    d = agent.diagnose(BugReport(symptom="anything at all"), notify=False)
    assert d.status == "novel"
    assert d.confidence == 0.0
