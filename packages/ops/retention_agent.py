"""Retention Agent: RSVP math + reminder plan + retention tracker."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from packages.shared import visibility
from . import _common
from ._common import DATA_DIR, DOCS_DIR, rel

RETENTION_COLUMNS = [
    "name", "rsvp_status", "accepted_date", "calendar_invite_sent",
    "reminder_48h_sent", "day_of_reminder_sent", "show_up_probability",
    "risk_level", "recommended_action",
]


def _show_up_rate(curated: bool) -> float:
    return 0.75 if curated else 0.6


def _risk(person: dict[str, Any]) -> tuple[float, str, str]:
    status = (person.get("rsvp_status") or "no_response").lower()
    priority = (person.get("priority") or "").lower()
    if status == "accepted":
        # Assume accepted-but-not-confirmed = 0.7; warm them up.
        prob = 0.85 if priority == "high" else 0.7
        risk = "low" if prob >= 0.8 else "medium"
        action = "Send calendar invite + 48h reminder"
        if priority == "high":
            action += " + personal nudge day-of"
        return prob, risk, action
    if status == "maybe":
        return 0.4, "high", "Personal nudge from organizer; offer +1 / introduce expected attendees"
    if status == "declined":
        return 0.0, "n/a", "Move on"
    # no_response
    return 0.2, "high" if priority == "high" else "medium", "Bump message; try second channel"


def run(event_state: dict[str, Any]) -> dict[str, Any]:
    _common.ensure_dirs()
    run_id = visibility.create_run_id("retention_agent")
    event = event_state.get("event", {}) or {}

    target = int(event.get("target_size") or 100)
    curated = bool(event.get("format")) or True  # default to curated/private
    show_up = _show_up_rate(curated)
    accepted_target = int(round(target / show_up))

    guests = _common.read_csv(DATA_DIR / "guest_crm.csv")
    rows: list[dict[str, Any]] = []
    high_risk = 0
    for g in guests:
        prob, risk, action = _risk(g)
        if risk == "high":
            high_risk += 1
        rows.append({
            "name": g.get("name", ""),
            "rsvp_status": g.get("rsvp_status", "no_response"),
            "accepted_date": g.get("accepted_date", ""),
            "calendar_invite_sent": "false",
            "reminder_48h_sent": "false",
            "day_of_reminder_sent": "false",
            "show_up_probability": f"{prob:.2f}",
            "risk_level": risk,
            "recommended_action": action,
        })

    tracker_path = DATA_DIR / "retention_tracker.csv"
    plan_path = DOCS_DIR / "retention_plan.md"
    _common.write_csv(tracker_path, RETENTION_COLUMNS, rows)

    plan = (
        f"# Retention Plan\n\n"
        f"- Target attendance: **{target}**\n"
        f"- Assumed show-up rate (curated/private): **{int(show_up*100)}%**\n"
        f"- Accepted RSVPs needed: **~{accepted_target}**\n\n"
        f"## Reminder cadence\n"
        f"- On accept: send calendar invite within 24h\n"
        f"- T-48h: reminder email + add-to-calendar link\n"
        f"- T-24h: personal nudge for high-priority guests\n"
        f"- Day-of: morning reminder + venue/parking details\n\n"
        f"## Current state\n"
        f"- Guests tracked: {len(rows)}\n"
        f"- High-risk (needs personal touch): {high_risk}\n"
    )
    plan_path.write_text(plan)

    event_state.setdefault("ops", {})["retention_plan"] = rows

    visibility.log_agent_run(
        agent_name="retention_agent",
        run_id=run_id,
        input_summary=f"target={target}, guests_tracked={len(rows)}",
        output_summary=f"need ~{accepted_target} accepted RSVPs at {int(show_up*100)}% show-up; {high_risk} high-risk",
        decisions_made=[
            f"Show-up assumption {int(show_up*100)}% (curated/private default)",
            f"Accepted-RSVP target = ceil(target / show_up) = {accepted_target}",
        ],
        reasoning_summary=(
            "Retention math drives invite volume. Curated rooms run higher show-up than open events; "
            "we still over-invite to absorb declines and no-shows."
        ),
        confidence="medium",
        files_read=[rel(DATA_DIR / "guest_crm.csv")] if guests else [],
        files_written=[rel(tracker_path), rel(plan_path)],
        blockers=[],
        next_actions=[
            f"Confirm {accepted_target} accepted RSVPs by T-3d",
            "Personally nudge high-risk high-priority guests at T-24h",
        ],
        event_state=event_state,
    )
    return {"target": target, "accepted_target": accepted_target, "tracked": len(rows), "high_risk": high_risk}
