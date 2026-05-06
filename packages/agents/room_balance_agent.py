"""Room Balance Agent — analyzes ranked prospects vs. target persona mix.

Produces breakdown, gaps, overrepresented groups, and sourcing recommendations.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Optional

from packages.shared.visibility import create_run_id, log_agent_run


AGENT_NAME = "room_balance_agent"


# Target percentages for the AI builder event archetype.
def pick_target_mix(event_state: dict | None) -> dict[str, float]:
    """Pick target mix from the LLM-designed audience stored in event_state.

    Falls back to evenly-distributed weights across the ICP personas if the
    designer didn't supply one.
    """
    if not event_state:
        return {}
    intel = event_state.get("intelligence", {}) or {}
    rb = intel.get("room_balance", {}) or {}
    mix = rb.get("target_mix") or {}
    if mix:
        return mix
    # fallback: even split across the ICP personas
    icp = intel.get("audience_icp", []) or []
    if not icp:
        return {}
    share = 1.0 / len(icp)
    return {p.get("name", f"persona_{i}"): share for i, p in enumerate(icp)}


def _persona_of(person: dict[str, Any]) -> str:
    p = person.get("persona") or ""
    if p:
        return p
    tags = person.get("tags") or []
    if isinstance(tags, list):
        for t in tags:
            if isinstance(t, str) and not t.startswith("avoid:"):
                return t
    return "unknown"


def run(ranked_prospects: list[dict[str, Any]],
        target_mix: Optional[dict[str, float]] = None,
        target_size: int = 100,
        event_state: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    run_id = create_run_id(AGENT_NAME)
    target_mix = target_mix or pick_target_mix(event_state)

    # Consider only the top target_size prospects as the "current room".
    top = [p for p in ranked_prospects if p.get("priority") != "needs_review"][:target_size]
    counts = Counter(_persona_of(p) for p in top)
    total = sum(counts.values()) or 1

    breakdown = dict(counts)
    pct = {k: round(v / total, 3) for k, v in counts.items()}

    gaps = []
    overrepresented = []
    for persona, target_pct in target_mix.items():
        actual_pct = pct.get(persona, 0)
        actual_n = counts.get(persona, 0)
        target_n = int(round(target_pct * target_size))
        if actual_n < target_n * 0.7:
            gaps.append({
                "persona": persona,
                "current": actual_n,
                "target": target_n,
                "deficit": target_n - actual_n,
            })
        elif actual_n > target_n * 1.3:
            overrepresented.append({
                "persona": persona,
                "current": actual_n,
                "target": target_n,
                "excess": actual_n - target_n,
            })

    gaps.sort(key=lambda g: g["deficit"], reverse=True)
    top_gap = gaps[0] if gaps else None

    recommendations = []
    for g in gaps[:3]:
        if g["persona"] == "ai_infra_builder":
            recommendations.append(
                "Source from GitHub contributors to popular agent/LLM tooling repos and AI infra Slacks."
            )
        elif g["persona"] == "ai_agent_founder":
            recommendations.append(
                "Source from YC W24/S24 AI agent batch and recent agent-startup launch posts."
            )
        elif g["persona"] == "technical_operator":
            recommendations.append(
                "Source from applied-AI / ML lead roles at Series A-C startups via warm intros."
            )
        elif g["persona"] == "community_connector":
            recommendations.append(
                "Source from prolific AI infra writers, podcast hosts, and Luma organizers in city."
            )
        else:
            recommendations.append(f"Source more {g['persona']} (need {g['deficit']} more).")

    if not gaps and not overrepresented:
        summary = f"Room is well-balanced across {len(counts)} personas ({total} prospects in top cut)."
    else:
        gap_str = ", ".join(g["persona"] for g in gaps[:2]) or "none"
        over_str = ", ".join(o["persona"] for o in overrepresented[:2]) or "none"
        summary = (
            f"Top {total} prospects: gaps in {gap_str}; overrepresented: {over_str}."
        )

    out = {
        "summary": summary,
        "persona_breakdown": breakdown,
        "persona_pct": pct,
        "target_mix": target_mix,
        "gaps": gaps,
        "overrepresented": overrepresented,
        "recommendations": recommendations,
        "top_gap": top_gap,
    }

    if event_state is not None:
        event_state.setdefault("intelligence", {})["room_balance"] = out

    log_agent_run(
        AGENT_NAME,
        run_id=run_id,
        input_summary=f"{len(ranked_prospects)} ranked prospects; target_size={target_size}.",
        output_summary=summary,
        decisions_made=[
            f"Compared top {total} non-flagged prospects against target mix.",
            f"Identified {len(gaps)} persona gap(s).",
        ],
        reasoning_summary=(
            "Room balance compares actual persona counts in the top cut to the target mix. "
            "A persona is 'gap' if it has <70% of its target slot, and 'overrepresented' at >130%."
        ),
        confidence="medium",
        next_actions=(
            ["Run sourcing pass focused on top-gap persona."] if top_gap else ["Proceed to outreach prioritization."]
        ),
        event_state=event_state,
    )

    return out
