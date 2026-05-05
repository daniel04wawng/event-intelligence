"""End-to-end Event Intelligence pipeline.

Run with:
    python -m packages.agents.run_intelligence

Inputs (defaults):
    data/event_brief.txt
    data/people_seed.csv  (optional)

Outputs:
    data/event_state.json
    data/ranked_people.csv
    docs/intelligence_summary.md
    docs/agent_activity_log.md  (appended)
    logs/agent_runs.jsonl       (appended)
    docs/structure_map.md       (kept in sync if missing)
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.shared.event_state import empty_event_state, save_event_state
from packages.shared.io import (
    read_event_brief,
    write_ranked_people_csv,
)
from packages.shared.visibility import create_run_id, log_agent_run
from packages.agents import (
    objective_agent,
    audience_agent,
    sourcing_agent,
    room_balance_agent,
)
from packages.scoring.attendee_fit import score_all


# --- Default paths ---
BRIEF_PATH = "data/event_brief.txt"
SEED_CSV = "data/people_seed.csv"
EVENT_STATE_PATH = "data/event_state.json"
RANKED_CSV = "data/ranked_people.csv"
SUMMARY_MD = "docs/intelligence_summary.md"
STRUCTURE_MAP = "docs/structure_map.md"


def _write_intelligence_summary(state: dict[str, Any], path: str = SUMMARY_MD) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ev = state.get("event", {})
    intel = state.get("intelligence", {})
    people = state.get("people", {})
    ranked = people.get("ranked_prospects", [])
    rb = intel.get("room_balance", {})
    open_qs = state.get("state", {}).get("open_questions", [])

    lines = [
        "# Event Intelligence Summary",
        "",
        f"_Generated {datetime.now(timezone.utc).isoformat()}_",
        "",
        "## 1. Event Objective",
        f"- **Goal:** {ev.get('goal', '')}",
        f"- **Format:** {ev.get('format', '')}",
        f"- **City:** {ev.get('city', '')}",
        f"- **Target size:** {ev.get('target_size', '')}",
        "- **Success metrics:**",
        *[f"  - {m}" for m in ev.get("success_metrics", [])],
        "",
        "## 2. Target Audience (ICP)",
        *[f"- **{p['name']}** (weight {p['weight']}): {p['description']}"
          for p in intel.get("audience_icp", [])],
        "",
        "## 3. Avoid Personas",
        *[f"- **{p['name']}** (penalty {p['penalty']}): {p['description']}"
          for p in intel.get("avoid_personas", [])],
        "",
        "## 4. Sourcing Strategy",
    ]
    for s in intel.get("sourcing_strategy", []):
        lines.append(f"### {s.get('type', '')}")
        for item in s.get("items", []):
            if isinstance(item, dict):
                lines.append(f"- {item.get('channel', item)} (priority: {item.get('priority', '-')})")
            else:
                lines.append(f"- {item}")
        lines.append("")

    rubric = intel.get("scoring_rubric", {})
    lines += [
        "## 5. Scoring Rubric",
        f"- **Max score:** {rubric.get('max_score', 100)}",
        f"- **High threshold:** {rubric.get('thresholds', {}).get('high', 75)}",
        f"- **Medium threshold:** {rubric.get('thresholds', {}).get('medium', 55)}",
        f"- **Notes:** {rubric.get('notes', '')}",
        "",
        "## 6. Top 10 Ranked Prospects",
        "| # | Name | Company | Role | Persona | Fit | Priority |",
        "|---|------|---------|------|---------|-----|----------|",
    ]
    for i, p in enumerate(ranked[:10], 1):
        lines.append(
            f"| {i} | {p.get('name','')} | {p.get('company','')} | {p.get('role','')} "
            f"| {p.get('persona','')} | {p.get('fit_score','')} | {p.get('priority','')} |"
        )
    lines += [
        "",
        "## 7. Room Balance",
        f"- **Summary:** {rb.get('summary', '')}",
        f"- **Persona breakdown:** {rb.get('persona_breakdown', {})}",
        "- **Gaps:**",
        *[f"  - {g['persona']}: current {g['current']} / target {g['target']} (deficit {g['deficit']})"
          for g in rb.get("gaps", [])],
        "- **Recommendations:**",
        *[f"  - {r}" for r in rb.get("recommendations", [])],
        "",
        "## 8. Open Questions",
        *[f"- {q}" for q in open_qs],
        "",
        "## 9. Next Recommended Ops Actions",
        "- Approve the top high-priority prospects in `data/ranked_people.csv`.",
        "- Hand `data/event_state.json` and `data/ranked_people.csv` to the Agentic Ops branch.",
        "- Run another sourcing pass focused on the top room-balance gap.",
        "",
    ]

    out_path.write_text("\n".join(lines) + "\n")


def _ensure_structure_map(path: str = STRUCTURE_MAP) -> None:
    """Touch the structure map only if missing — the canonical version lives
    in the repo and is human-edited. Pipeline appends a 'last run' marker."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    marker = f"\n\n<!-- last pipeline run: {datetime.now(timezone.utc).isoformat()} -->\n"
    if p.exists():
        # rewrite trailing marker
        existing = p.read_text()
        if "<!-- last pipeline run:" in existing:
            head = existing.split("<!-- last pipeline run:")[0].rstrip()
            p.write_text(head + marker)
        else:
            with p.open("a") as f:
                f.write(marker)


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    brief_path = argv[0] if len(argv) > 0 else BRIEF_PATH
    seed_path = argv[1] if len(argv) > 1 else SEED_CSV

    pipeline_run_id = create_run_id("run_intelligence")
    state = empty_event_state()
    state["event"]["name"] = "AI Builder Event MVP"

    brief = read_event_brief(brief_path)
    if not brief:
        print(f"[run_intelligence] No brief found at {brief_path}; aborting.", file=sys.stderr)
        return 2

    # 1. Objective
    objective = objective_agent.run(brief, event_state=state)
    # 2. Audience
    audience = audience_agent.run(objective, event_state=state)
    # 3. Sourcing (ingests seed CSV if present)
    sourcing = sourcing_agent.run(
        objective, audience,
        seed_csv_path=seed_path if Path(seed_path).exists() else None,
        event_state=state,
    )

    # 4. Score prospects
    prospects = state.get("people", {}).get("prospects", []) or sourcing.get("prospects", [])
    ranked = score_all(
        prospects,
        audience.get("audience_icp", []),
        audience.get("scoring_rubric", {}),
        objective,
        avoid_personas=audience.get("avoid_personas", []),
    )
    state.setdefault("people", {})["ranked_prospects"] = ranked

    # 5. Room balance
    room_balance_agent.run(ranked, target_size=objective.get("target_size", 100), event_state=state)

    # Write outputs
    files_written: list[str] = []
    save_event_state(EVENT_STATE_PATH, state)
    files_written.append(EVENT_STATE_PATH)
    write_ranked_people_csv(RANKED_CSV, ranked)
    files_written.append(RANKED_CSV)
    _write_intelligence_summary(state, SUMMARY_MD)
    files_written.append(SUMMARY_MD)
    _ensure_structure_map(STRUCTURE_MAP)
    files_written.append(STRUCTURE_MAP)

    # Update visibility pointer in state
    state.setdefault("visibility", {})["latest_summary_files"] = [SUMMARY_MD, STRUCTURE_MAP]
    save_event_state(EVENT_STATE_PATH, state)

    high = [p for p in ranked if p.get("priority") == "high"]
    rb = state.get("intelligence", {}).get("room_balance", {})
    top_gap = rb.get("top_gap")

    log_agent_run(
        "run_intelligence",
        run_id=pipeline_run_id,
        input_summary=f"brief={brief_path}, seed={seed_path if Path(seed_path).exists() else 'none'}",
        output_summary=(
            f"Pipeline complete: {len(ranked)} prospects scored, "
            f"{len(high)} high-priority, top_gap={top_gap['persona'] if top_gap else 'none'}."
        ),
        decisions_made=["Ran objective → audience → sourcing → scoring → room_balance pipeline."],
        reasoning_summary="Sequential pipeline; each stage writes to event_state and emits its own visibility trace.",
        confidence="medium",
        files_read=[brief_path] + ([seed_path] if Path(seed_path).exists() else []),
        files_written=files_written,
        next_actions=["Hand event_state.json + ranked_people.csv to Agentic Ops branch."],
        event_state=state,
    )
    save_event_state(EVENT_STATE_PATH, state)

    # Console summary
    print()
    print("=" * 60)
    print("Event Intelligence pipeline complete.")
    print("=" * 60)
    print(f"Prospects scored      : {len(ranked)}")
    print(f"High-priority         : {len(high)}")
    print(f"Top room-balance gap  : {top_gap['persona'] if top_gap else 'none'}")
    print("Files written         :")
    for f in files_written:
        print(f"  - {f}")
    print("  - logs/agent_runs.jsonl")
    print("  - docs/agent_activity_log.md")
    print()
    print("Next: python -m packages.ops.run_ops")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
