"""Audience Intelligence Agent.

Calls the LLM-powered audience designer to derive ICP personas, avoid personas,
scoring rubric, target room mix, approval criteria, and sourcing channels —
all tailored to the specific event proposal. No hardcoded theme libraries.

If the LLM is unavailable (no API key / no SDK), falls back to a minimal
generic library. The fallback is intentionally not theme-specific.
"""
from __future__ import annotations

from typing import Any, Optional

from packages.enrichment.audience_designer import design_audience
from packages.shared.visibility import create_run_id, log_agent_run


AGENT_NAME = "audience_agent"


def _compose_brief_for_audience(objective: dict[str, Any], event_brief: str) -> str:
    """Prepend explicit organizer triad so audience_designer weights ICPs correctly."""
    chunks: list[str] = []
    et = (objective.get("event_type") or objective.get("format") or "").strip()
    if et:
        chunks.append(f"## Event type\n{et}")
    want = (objective.get("desired_attendees") or "").strip()
    if want:
        chunks.append(f"## Who we want in the room\n{want}")
    goal = (objective.get("goal") or "").strip()
    if goal:
        chunks.append(f"## Overall goal\n{goal}")
    body = (event_brief or "").strip()
    if not chunks:
        return body
    return "\n\n".join(chunks) + "\n\n---\n\n## Full organizer message\n" + body


def run(objective: dict[str, Any],
        event_state: Optional[dict[str, Any]] = None,
        event_brief: str = "",
        *,
        persist_visibility: bool = True) -> dict[str, Any]:
    run_id = create_run_id(AGENT_NAME)
    event_type = objective.get("event_type", "")
    city = objective.get("city", "")

    effective_brief = _compose_brief_for_audience(objective, event_brief)
    audience, designer_telemetry = design_audience(effective_brief)

    icp = audience.get("audience_icp", [])
    avoid = audience.get("avoid_personas", [])
    scoring_rubric = audience.get("scoring_rubric", {})
    target_mix = audience.get("target_mix", {})
    approval_criteria = audience.get("approval_criteria", [])
    data_to_collect = audience.get("data_to_collect", [])
    sourcing_channels = audience.get("sourcing_channels", [])

    out = {
        "audience_icp": icp,
        "avoid_personas": avoid,
        "approval_criteria": approval_criteria,
        "data_to_collect": data_to_collect,
        "sourcing_channels": sourcing_channels,
        "scoring_rubric": scoring_rubric,
        "target_mix": target_mix,
    }

    if event_state is not None:
        intel = event_state.setdefault("intelligence", {})
        intel["audience_icp"] = icp
        intel["avoid_personas"] = avoid
        intel["scoring_rubric"] = scoring_rubric
        # stash target mix here so room_balance_agent picks it up later
        rb = intel.setdefault("room_balance", {})
        rb["target_mix"] = target_mix
        intel.setdefault("notes", []).append(
            f"Audience designer status: {designer_telemetry.get('status')}. "
            f"Personas: {len(icp)}; avoid: {len(avoid)}."
        )

    log_agent_run(
        AGENT_NAME,
        run_id=run_id,
        input_summary=(
            f"Objective for '{event_type}' in {city or 'unspecified city'}; "
            f"effective brief len={len(effective_brief)}."
        ),
        output_summary=(
            f"Audience designer status={designer_telemetry.get('status')}; "
            f"defined {len(icp)} ICP personas, {len(avoid)} avoid personas; "
            f"target_mix has {len(target_mix)} entries."
        ),
        decisions_made=[
            f"Designer mode: {designer_telemetry.get('status')}.",
            f"ICP personas: {[p.get('name') for p in icp]}.",
            f"High-fit threshold: {scoring_rubric.get('thresholds', {}).get('high', 75)}.",
        ],
        reasoning_summary=(
            "Audience design uses an organizer triad when present (event type, who belongs "
            "in the room, overall goal) prepended to the full brief, then one LLM pass — "
            "no hardcoded persona libraries. Rubric is rule-based downstream for auditability."
        ),
        confidence="high" if designer_telemetry.get("status") == "ok" else "low",
        next_actions=["Run sourcing_agent to define queries and (optionally) curate via web search."],
        event_state=event_state,
        persist_to_disk=persist_visibility,
    )

    return out
