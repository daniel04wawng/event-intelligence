"""Preview how agents interpret organizer input — no sourcing or curation.

Does not run sourcing_agent (no web search for prospects). Does not write
ranked_people.csv, event_state.json, or pipeline summaries.

Uses persist_visibility=False so logs/agent_runs.jsonl and docs/agent_activity_log.md
are not appended.

Examples:
  python -m packages.agents.preview_intent data/event_brief.txt
  python -m packages.agents.preview_intent - < my_notes.txt
  echo "Event type: salon ..." | python -m packages.agents.preview_intent -
  python -m packages.agents.preview_intent data/event_brief.txt --audience
  python -m packages.agents.preview_intent data/event_brief.txt -i   # prompt each open question
  python -m packages.agents.preview_intent brief.txt --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from packages.agents import audience_agent, objective_agent
from packages.agents.intent_extractor import extract_event_intent
from packages.shared.io import read_event_brief


def _open_questions_list(objective: dict[str, Any]) -> list[str]:
    oq = objective.get("open_questions")
    if isinstance(oq, list) and len(oq) > 0:
        return [str(x) for x in oq]
    return list(objective_agent.DEFAULT_OPEN_QUESTIONS)


def _tty_safe_input(prompt: str) -> str:
    """Read answer even when brief was piped on stdin (Unix /dev/tty)."""
    try:
        with open("/dev/tty", "r") as tty:
            print(prompt, end="", flush=True)
            line = tty.readline()
            return line.strip() if line else ""
    except OSError:
        return input(prompt).strip()


def _interactive_answers(questions: list[str]) -> dict[str, str]:
    if not questions:
        return {}
    print()
    print("*" * 60)
    print("INTERACTIVE — answer each question (Enter skips)")
    print("*" * 60)
    print()
    out: dict[str, str] = {}
    for i, q in enumerate(questions, 1):
        ans = _tty_safe_input(f"{i}. {q}\n   > ")
        if ans:
            out[q] = ans
    if out:
        print()
        print("--- Text you can paste back into your brief ---")
        for q, a in out.items():
            print(f"- {q} {a}")
        print()
    return out


def _load_brief(source: str) -> str:
    if source == "-":
        return sys.stdin.read().strip()
    p = Path(source)
    if not p.exists():
        print(f"[preview_intent] File not found: {source}", file=sys.stderr)
        sys.exit(2)
    return read_event_brief(p)


def _emit_json(intent: dict, objective: dict, audience: dict[str, Any] | None) -> None:
    payload: dict[str, Any] = {"intent": intent, "objective": objective}
    if audience is not None:
        payload["audience"] = audience
    print(json.dumps(payload, indent=2, default=str))


def _intent_extractor_blank(intent: dict) -> bool:
    keys = ("event_type", "desired_attendees", "overall_goal", "target_size", "city", "event_name")
    return all(not str(intent.get(k) or "").strip() for k in keys)


def _dash(v: Any) -> str:
    s = str(v).strip() if v is not None else ""
    return s if s else "—"


def _emit_human(
    intent: dict,
    objective: dict,
    audience: dict[str, Any] | None,
    *,
    questions_for_interactive: list[str] | None = None,
    verbose: bool = False,
) -> None:
    print()
    print("=" * 60)
    print("PREVIEW — interpretation only (no prospect curation)")
    print("=" * 60)
    if verbose:
        print(f"(module: {Path(__file__).resolve()})", flush=True)
    print()

    extractor_empty = _intent_extractor_blank(intent)
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

    # Single merged view — avoids “all dashes” when only keyword heuristics filled fields.
    et = _dash(intent.get("event_type") or objective.get("event_type"))
    attendees = _dash(intent.get("desired_attendees") or objective.get("desired_attendees"))
    goal = _dash(intent.get("overall_goal") or objective.get("goal"))

    print("ORGANIZER INTENT (triad)")
    print("-" * 40)
    print(f"  Event type:        {et}")
    print(f"  Who we want:       {attendees}")
    print(f"  Overall goal:      {goal}")
    print()

    print("LOGISTICS (objective_agent heuristics)")
    print("-" * 40)
    print(f"  Target size:       {_dash(objective.get('target_size'))}")
    print(f"  City:              {_dash(objective.get('city'))}")
    print(f"  Event name:        {_dash(objective.get('event_name'))}")
    print()

    if extractor_empty:
        print(
            "Note: The intent extractor had nothing structured to parse "
            "(no ANTHROPIC_API_KEY or no labeled sections like "
            "`Event type:` / `People we want:` — see data/event_brief.template.txt). "
            "Fields above still use keyword/heuristic inference from your full paragraph."
        )
        print()
    elif not has_key:
        print(
            "Note: Using labeled-section parsing only (no ANTHROPIC_API_KEY). "
            "Set the key for richer triad extraction from free-form prose."
        )
        print()
    oq = questions_for_interactive if questions_for_interactive is not None else _open_questions_list(objective)
    print()
    print("*" * 60)
    print("OPEN QUESTIONS — gaps to clarify before you run full curation")
    print("*" * 60)
    for i, q in enumerate(oq, 1):
        print(f"  {i}. {q}")
    print()
    print("Tip: run with --interactive to answer these in the terminal.")
    sm = objective.get("success_metrics") or []
    if sm:
        print()
        print("## Default success metrics (from objective_agent)")
        for m in sm:
            print(f"- {m}")
    print()
    if audience is None:
        print("(Skipping audience / ICP design. Pass --audience to run audience_agent — uses LLM, costs tokens.)")
        print()
        return

    print("## Audience design preview (audience_agent → design_audience)")
    print(f"- **ICP personas ({len(audience.get('audience_icp', []))}):**")
    for p in audience.get("audience_icp", []):
        print(f"  - **{p.get('name')}** (weight {p.get('weight')}): {p.get('description', '')}")
    print(f"- **Avoid personas ({len(audience.get('avoid_personas', []))}):**")
    for p in audience.get("avoid_personas", []):
        print(f"  - **{p.get('name')}** (penalty {p.get('penalty')}): {p.get('description', '')}")
    rubric = audience.get("scoring_rubric") or {}
    th = (rubric.get("thresholds") or {})
    print(f"- **Score thresholds:** high={th.get('high')}, medium={th.get('medium')}, low={th.get('low')}")
    mix = audience.get("target_mix") or {}
    print(f"- **Target mix:** {len(mix)} persona buckets")
    print()


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(
        description="Preview intent + objective interpretation without running curation.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        default="data/event_brief.txt",
        help="Path to brief text file, or '-' for stdin (default: data/event_brief.txt)",
    )
    parser.add_argument(
        "--audience",
        action="store_true",
        help="Also run audience_agent (LLM personas). Still no web-search curation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of Markdown-style text.",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="After showing the preview, prompt each open question in the terminal.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print path to this preview_intent.py (confirms which checkout runs).",
    )
    args = parser.parse_args(argv)

    brief = _load_brief(args.source)
    if not brief:
        print("[preview_intent] Empty brief.", file=sys.stderr)
        return 2

    intent = extract_event_intent(brief)
    objective = objective_agent.run(
        brief,
        event_state=None,
        intent=intent,
        persist_visibility=False,
    )

    audience_out: dict[str, Any] | None = None
    if args.audience:
        audience_out = audience_agent.run(
            objective,
            event_state=None,
            event_brief=brief,
            persist_visibility=False,
        )

    questions = _open_questions_list(objective)

    if args.json:
        if args.interactive:
            print("[preview_intent] --interactive ignored with --json", file=sys.stderr)
        _emit_json(intent, objective, audience_out)
        return 0

    _emit_human(
        intent,
        objective,
        audience_out,
        questions_for_interactive=questions,
        verbose=args.verbose,
    )

    if args.interactive:
        _interactive_answers(questions)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
