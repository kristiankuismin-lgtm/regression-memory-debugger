"""Command-line interface.

    python -m regression_debugger.cli seed         # load seed bugs into memory
    python -m regression_debugger.cli query "..."  # diagnose an incoming bug
    python -m regression_debugger.cli list          # show what's in memory
    python -m regression_debugger.cli demo          # scripted before/after demo
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from regression_debugger.agent import RegressionAgent
from regression_debugger.config import backend_summary, build_agent
from regression_debugger.memory.local import LocalMemoryStore
from regression_debugger.notify.slack import SlackNotifier
from regression_debugger.patch.local import LocalPatchApplier
from regression_debugger.types import BugReport, MemoryEntry

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed_bugs.json"

# --- tiny ANSI helpers (no dependency) -------------------------------------
def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if sys.stdout.isatty() else s

def bold(s): return _c("1", s)
def green(s): return _c("32", s)
def yellow(s): return _c("33", s)
def cyan(s): return _c("36", s)
def dim(s): return _c("2", s)


def _load_seed() -> list[MemoryEntry]:
    raw = json.loads(SEED.read_text(encoding="utf-8"))
    return [MemoryEntry.from_dict(d) for d in raw]


def _print_verdict(d) -> None:
    if d.is_known:
        print(green(bold(f"\n  ✔ KNOWN REGRESSION  ({d.confidence:.0%} match)")))
    else:
        print(yellow(bold(f"\n  ✦ NEW BUG  (best match {d.confidence:.0%})")))
    print(dim("  " + "-" * 56))
    for line in d.answer.splitlines():
        print("  " + line)
    if d.suggested_patch:
        print(cyan(f"\n  → patch proposal: {d.suggested_patch}"))
    print()


def cmd_seed(_args) -> None:
    agent = build_agent()
    entries = _load_seed()
    for e in entries:
        agent.learn(e)
    print(green(f"Seeded {len(entries)} resolved bugs into memory."))
    print(dim(f"backend: {backend_summary()}"))


def cmd_list(_args) -> None:
    agent = build_agent()
    entries = agent.memory.all()
    if not entries:
        print(yellow("Memory is empty. Run `seed` first."))
        return
    for e in entries:
        print(f"{bold(e.id):>22}  {e.title}")


def cmd_query(args) -> None:
    agent = build_agent()
    bug = BugReport(symptom=args.text, title=args.title or "", source="cli")
    d = agent.diagnose(bug)
    _print_verdict(d)


def cmd_demo(_args) -> None:
    """Self-contained scripted demo on an isolated temp memory."""
    tmp = Path(tempfile.mkdtemp()) / "demo_memory.json"
    agent = RegressionAgent(
        memory=LocalMemoryStore(tmp),
        patcher=LocalPatchApplier(out_dir=tmp.parent / "patches"),
        notifier=SlackNotifier(None),
    )

    print(bold("\n=== Regression Memory Debugger — live demo ===\n"))
    print("Memory starts empty. The agent has never seen any bug.\n")

    bug1 = BugReport(
        title="Duplicate companies in search results",
        symptom=("Search for Nordic road-transport targets returns the same "
                 "company three times with slightly different names."),
        source="produck",
    )
    print(bold("1) A bug comes in:"), bug1.title)
    d1 = agent.diagnose(bug1, notify=False)
    _print_verdict(d1)
    input(dim("   [enter] teach the agent the fix the team shipped...")) if sys.stdin.isatty() else None

    agent.learn(MemoryEntry(
        id="BUG-1042",
        title="Duplicate companies in search results",
        symptom=bug1.symptom,
        root_cause="Dedup key used company name only; normalized-name collisions slipped through.",
        fix="Switch dedup key to canonical domain + registry id; add fuzzy-name fold.",
        files=["search/dedup.ts", "search/normalize.ts"],
        tags=["search", "dedup"],
    ))
    print(green("\n   ✔ Fix recorded to long-term memory.\n"))

    bug2 = BugReport(
        title="Same firm appears multiple times in results",
        symptom=("Utility-contractor search in Michigan shows one contractor "
                 "listed several times under near-identical names."),
        source="slack",
    )
    print(bold("2) Weeks later, a DIFFERENT user reports what looks new:"), bug2.title)
    d2 = agent.diagnose(bug2)
    _print_verdict(d2)
    print(dim("   ^ The agent recognized a paraphrased recurrence and recalled the fix —\n"
              "     something only possible because it remembered.\n"))

    bug3 = BugReport(
        title="Slack digest not arriving",
        symptom="The daily frustration-signal digest stopped posting to the channel.",
        source="slack",
    )
    print(bold("3) A genuinely unrelated bug:"), bug3.title)
    d3 = agent.diagnose(bug3, notify=False)
    _print_verdict(d3)
    print(dim("   ^ Correctly flagged as new — it doesn't pattern-match everything.\n"))
    print(bold("=== end demo ===\n"))


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="regression-debugger")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("seed", help="load seed bugs into memory").set_defaults(fn=cmd_seed)
    sub.add_parser("list", help="list memory contents").set_defaults(fn=cmd_list)
    sub.add_parser("demo", help="run the scripted before/after demo").set_defaults(fn=cmd_demo)

    q = sub.add_parser("query", help="diagnose an incoming bug")
    q.add_argument("text", help="the bug symptom text")
    q.add_argument("--title", default="", help="optional short title")
    q.set_defaults(fn=cmd_query)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
