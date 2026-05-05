"""Outreach Agent: turns ranked_people.csv into a draft outreach queue + guest CRM."""
from __future__ import annotations

from typing import Any

from packages.shared import visibility
from packages.shared.io import load_people_csv
from . import _common
from ._common import DATA_DIR, RANKED_PEOPLE_PATH, rel

OUTREACH_COLUMNS = [
    "name", "company", "role", "channel", "priority", "fit_score",
    "outreach_angle", "message", "follow_up_message", "status",
    "last_touch", "notes",
]
GUEST_CRM_COLUMNS = [
    "name", "company", "role", "email", "linkedin_url", "priority", "fit_score",
    "channel", "status", "last_touch", "rsvp_status", "notes",
]


def _channel_for(person: dict[str, Any]) -> str:
    if person.get("email"):
        return "email"
    if person.get("linkedin_url"):
        return "linkedin"
    return "poke"


def _priority(person: dict[str, Any]) -> str:
    p = (person.get("priority") or "").lower()
    if p in {"high", "medium", "low"}:
        return p
    try:
        score = float(person.get("fit_score") or 0)
    except (TypeError, ValueError):
        score = 0
    if score >= 0.75:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def _angle(person: dict[str, Any]) -> str:
    return (person.get("outreach_angle") or person.get("why_relevant")
            or f"{person.get('role','operator')} at {person.get('company','your company')}").strip()


def _message(person: dict[str, Any], event: dict[str, Any]) -> str:
    name = (person.get("name") or "there").split()[0]
    angle = _angle(person)
    city = event.get("city") or "SF"
    goal = event.get("goal") or "agent infrastructure and devtools"
    return (
        f"Hey {name}, saw your work on {angle}. I'm putting together a small AI builders "
        f"event in {city} next week for founders/operators working around {goal}. "
        f"Thought you'd be a strong fit for the room — would love to have you if you're around."
    )


def _follow_up(person: dict[str, Any]) -> str:
    name = (person.get("name") or "there").split()[0]
    return f"Hey {name}, bumping this — happy to send the details if you're potentially around."


def _subject(person: dict[str, Any], event: dict[str, Any]) -> str:
    return f"Small AI builders night in {event.get('city') or 'SF'} next week — thought of you"


def run(event_state: dict[str, Any]) -> dict[str, Any]:
    _common.ensure_dirs()
    run_id = visibility.create_run_id("outreach_agent")
    event = event_state.get("event", {}) or {}

    people = load_people_csv(RANKED_PEOPLE_PATH) if RANKED_PEOPLE_PATH.exists() else []
    if not people:
        people = (event_state.get("people", {}) or {}).get("ranked_prospects", []) or []

    queue: list[dict[str, Any]] = []
    crm: list[dict[str, Any]] = []
    high = med = low = 0
    for p in people:
        prio = _priority(p)
        if prio == "high": high += 1
        elif prio == "medium": med += 1
        else: low += 1
        channel = _channel_for(p)
        msg = _message(p, event)
        if channel == "email":
            msg = f"Subject: {_subject(p, event)}\n\n{msg}"
        queue.append({
            "name": p.get("name", ""),
            "company": p.get("company", ""),
            "role": p.get("role", ""),
            "channel": channel,
            "priority": prio,
            "fit_score": p.get("fit_score", ""),
            "outreach_angle": _angle(p),
            "message": msg,
            "follow_up_message": _follow_up(p),
            "status": "draft_ready",
            "last_touch": "",
            "notes": "",
        })
        crm.append({
            "name": p.get("name", ""),
            "company": p.get("company", ""),
            "role": p.get("role", ""),
            "email": p.get("email", ""),
            "linkedin_url": p.get("linkedin_url", ""),
            "priority": prio,
            "fit_score": p.get("fit_score", ""),
            "channel": channel,
            "status": "draft_ready",
            "last_touch": "",
            "rsvp_status": "no_response",
            "notes": p.get("notes", ""),
        })

    out_queue = DATA_DIR / "outreach_queue.csv"
    out_crm = DATA_DIR / "guest_crm.csv"
    _common.write_csv(out_queue, OUTREACH_COLUMNS, queue)
    _common.write_csv(out_crm, GUEST_CRM_COLUMNS, crm)

    event_state.setdefault("ops", {})["outreach_queue"] = queue

    visibility.log_agent_run(
        agent_name="outreach_agent",
        run_id=run_id,
        input_summary=f"{len(people)} ranked prospects",
        output_summary=f"{len(queue)} drafts (high={high}, med={med}, low={low})",
        decisions_made=[
            "Channel: email if email present, else linkedin if profile present, else poke/manual",
            "Priority bucketed from explicit field or fit_score thresholds (>=.75 high, >=.5 medium)",
        ],
        reasoning_summary=(
            "Generate channel-appropriate drafts with a short personal angle per prospect; do not "
            "send. Tone is casual/high-signal, suited to an SF builder community."
        ),
        confidence="medium",
        files_read=[rel(RANKED_PEOPLE_PATH)] if RANKED_PEOPLE_PATH.exists() else [],
        files_written=[rel(out_queue), rel(out_crm)],
        blockers=[] if people else ["No ranked prospects to draft outreach for"],
        next_actions=[
            f"Review {min(high, 30)} high-priority drafts and approve for send",
            "Connect Gmail/Poke when ready (see packages/integrations stubs)",
        ],
        event_state=event_state,
    )
    return {"queue_count": len(queue), "high": high, "medium": med, "low": low}
