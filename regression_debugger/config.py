"""Environment-driven wiring.

Picks backends from env vars so you can flip from the offline demo to the real
Parcle + Enter + Slack stack without touching code:

    PARCLE_API_KEY     -> use Parcle long-term memory (else local JSON store)
    PARCLE_NAMESPACE   -> memory namespace / team id (default: regression-debugger)
    ENTER_API_URL      -> use Enter Pro to apply patches (else write locally)
    ENTER_API_KEY      -> Enter Pro auth
    ENTER_PROJECT      -> Enter project id
    SLACK_WEBHOOK_URL  -> post verdicts to Slack (else print preview)
    MEMORY_PATH        -> local store path (default: data/memory.json)
    KNOWN_THRESHOLD    -> confidence cutoff for "known regression"
"""

from __future__ import annotations

import os

from regression_debugger.agent import RegressionAgent
from regression_debugger.memory.base import MemoryStore
from regression_debugger.notify.slack import SlackNotifier
from regression_debugger.patch.base import PatchApplier
from regression_debugger.patch.enter import EnterPatchApplier
from regression_debugger.patch.local import LocalPatchApplier


def build_memory(memory_path: str | None = None) -> MemoryStore:
    if os.getenv("PARCLE_API_KEY"):
        from regression_debugger.memory.parcle_store import ParcleMemoryStore
        return ParcleMemoryStore(
            namespace=os.getenv("PARCLE_NAMESPACE", "regression-debugger"),
        )
    from regression_debugger.memory.local import LocalMemoryStore
    return LocalMemoryStore(memory_path or os.getenv("MEMORY_PATH", "data/memory.json"))


def build_patcher() -> PatchApplier:
    url, key = os.getenv("ENTER_API_URL"), os.getenv("ENTER_API_KEY")
    if url and key:
        return EnterPatchApplier(url, key, project=os.getenv("ENTER_PROJECT", ""))
    return LocalPatchApplier()


def build_agent(memory_path: str | None = None) -> RegressionAgent:
    threshold = float(os.getenv("KNOWN_THRESHOLD", "0.25"))
    return RegressionAgent(
        memory=build_memory(memory_path),
        patcher=build_patcher(),
        notifier=SlackNotifier(os.getenv("SLACK_WEBHOOK_URL")),
        known_threshold=threshold,
    )


def backend_summary() -> str:
    mem = "Parcle" if os.getenv("PARCLE_API_KEY") else "local JSON"
    patch = "Enter Pro" if (os.getenv("ENTER_API_URL") and os.getenv("ENTER_API_KEY")) else "local file"
    slack = "Slack webhook" if os.getenv("SLACK_WEBHOOK_URL") else "console preview"
    return f"memory={mem} | patch={patch} | notify={slack}"
