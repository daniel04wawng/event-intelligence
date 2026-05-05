"""Sourcing Agent — generates queries, sources, and ingests/normalizes seed CSV.

MVP intentionally avoids scraping. It produces actionable sourcing artifacts
(queries, channels, columns, prioritization rules) and normalizes any provided
seed CSV into the shared people schema.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from packages.shared.event_state import empty_person, PERSON_CSV_COLUMNS
from packages.shared.io import load_people_csv
from packages.shared.visibility import create_run_id, log_agent_run


AGENT_NAME = "sourcing_agent"


def _build_queries(objective: dict[str, Any], audience: dict[str, Any]) -> list[str]:
    city = objective.get("city", "")
    base = [
        "AI agent founders building production agent systems",
        "AI infra / devtools engineers shipping agent frameworks",
        "Applied AI leads at Series A-C startups",
        "Active GitHub contributors to popular agent / LLM tooling repos",
    ]
    if city:
        base = [f"{q} based in {city}" for q in base]
    base.append("High-signal community organizers in AI infra space")
    return base


def _ingest_seed(seed_path: Optional[str | Path]) -> list[dict[str, Any]]:
    if not seed_path:
        return []
    p = Path(seed_path)
    if not p.exists():
        return []
    raw = load_people_csv(p)
    out = []
    for r in raw:
        person = empty_person()
        for k in PERSON_CSV_COLUMNS:
            if r.get(k) not in (None, ""):
                person[k] = r[k]
        # carry forward any provided notes from extra columns
        extra = r.get("extra") if isinstance(r.get("extra"), dict) else None
        if extra and not person["notes"]:
            person["notes"] = "; ".join(f"{k}={v}" for k, v in extra.items())
        out.append(person)
    return out


def run(objective: dict[str, Any],
        audience: dict[str, Any],
        seed_csv_path: Optional[str | Path] = None,
        event_state: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    run_id = create_run_id(AGENT_NAME)

    queries = _build_queries(objective, audience)
    suggested_sources = audience.get("sourcing_channels", [])
    ideal_columns = PERSON_CSV_COLUMNS

    prioritization_rules = [
        "Warm intros and known builders go to top of queue.",
        "Founders/engineers actively building in-theme rank higher than investors.",
        "If two prospects tie on fit, prefer the one with stronger contribution signal (writing, OSS, talks).",
        "Cap any single company to ~3 attendees to keep room diverse.",
        "Reject anyone matching avoid personas regardless of company prestige.",
    ]

    prospects = _ingest_seed(seed_csv_path)
    files_read = [str(seed_csv_path)] if seed_csv_path and Path(seed_csv_path).exists() else []

    if event_state is not None:
        intel = event_state.setdefault("intelligence", {})
        intel.setdefault("sourcing_strategy", []).extend([
            {"type": "queries", "items": queries},
            {"type": "sources", "items": suggested_sources},
            {"type": "prioritization_rules", "items": prioritization_rules},
        ])
        if prospects:
            event_state.setdefault("people", {})["prospects"] = prospects

    log_agent_run(
        AGENT_NAME,
        run_id=run_id,
        input_summary=f"Objective + audience ICP. Seed CSV: {bool(prospects)} ({len(prospects)} rows).",
        output_summary=(
            f"Generated {len(queries)} sourcing queries, "
            f"normalized {len(prospects)} prospects from seed CSV."
        ),
        decisions_made=[
            f"Built {len(queries)} sourcing queries weighted to in-theme builders.",
            "Capped per-company attendance at ~3 to preserve room diversity.",
        ],
        reasoning_summary=(
            "MVP avoids live scraping; instead produces explicit queries and channels so a human "
            "(or the Agentic Ops branch) can run sourcing. Normalizing the seed CSV early makes "
            "downstream scoring deterministic."
        ),
        confidence="medium" if prospects else "low",
        files_read=files_read,
        next_actions=["Score prospects with packages/scoring/attendee_fit.py."],
        event_state=event_state,
    )

    return {
        "queries": queries,
        "suggested_sources": suggested_sources,
        "ideal_columns": ideal_columns,
        "prioritization_rules": prioritization_rules,
        "prospects": prospects,
    }
