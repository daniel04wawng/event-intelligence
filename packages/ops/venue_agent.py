"""Venue Agent: requirements, CRM template, outreach email draft."""
from __future__ import annotations

from typing import Any

from packages.shared import visibility
from . import _common
from ._common import DATA_DIR, DRAFTS_DIR, rel

VENUE_CRM_COLUMNS = [
    "venue_name", "contact_name", "contact_email", "location", "capacity",
    "estimated_cost", "availability", "food_policy", "av", "status",
    "last_touch", "reply_summary", "next_step",
]

SAMPLE_VENUES = [
    {"venue_name": "Shack15", "location": "SF Ferry Building", "capacity": "150", "notes": "founder community space"},
    {"venue_name": "Frontier Tower", "location": "SF SoMa", "capacity": "120", "notes": "AI/builder community"},
    {"venue_name": "South Park Commons", "location": "SF SoMa", "capacity": "100", "notes": "early-stage operator network"},
    {"venue_name": "The Pearl", "location": "SF Dogpatch", "capacity": "200", "notes": "event venue, paid"},
    {"venue_name": "AGI House", "location": "Hillsborough", "capacity": "80", "notes": "AI residency, may not fit"},
]


def _outreach_email(event: dict[str, Any]) -> str:
    city = event.get("city") or "SF"
    date = event.get("date") or "next week"
    size = event.get("target_size") or 100
    name = event.get("name") or "AI Builders Night"
    return f"""Subject: {name} — venue inquiry for ~{size} in {city}

Hi [contact],

We're hosting a curated AI builders event ({name}) in {city} on/around {date}.
Target attendance is ~{size}, mostly founders and operators in agent infra and devtools.
Format is light program (~20 min) + structured networking, evening only (6–9pm).

Could you share:
- Availability for the target date
- Standing capacity / max headcount
- Pricing (and any nonprofit/community rate)
- AV setup (mic, screen, projector)
- Outside food / catering policy (we'd likely cater light bites + drinks)
- Load-in window
- Insurance / security requirements
- Floor plan if available

Happy to come by for a walkthrough this week.

Thanks,
[Organizer]
"""


def run(event_state: dict[str, Any]) -> dict[str, Any]:
    _common.ensure_dirs()
    run_id = visibility.create_run_id("venue_agent")
    event = event_state.get("event", {}) or {}

    seed_path = DATA_DIR / "venue_seed.csv"
    seeds = _common.read_csv(seed_path) if seed_path.exists() else []
    files_read = [rel(seed_path)] if seeds else []
    if not seeds:
        seeds = SAMPLE_VENUES

    crm: list[dict[str, Any]] = []
    for v in seeds:
        crm.append({
            "venue_name": v.get("venue_name", ""),
            "contact_name": v.get("contact_name", ""),
            "contact_email": v.get("contact_email", ""),
            "location": v.get("location", ""),
            "capacity": v.get("capacity", ""),
            "estimated_cost": v.get("estimated_cost", ""),
            "availability": v.get("availability", "unknown"),
            "food_policy": v.get("food_policy", "unknown"),
            "av": v.get("av", "unknown"),
            "status": v.get("status", "to_contact"),
            "last_touch": "",
            "reply_summary": "",
            "next_step": "Send outreach email + request walkthrough",
        })

    crm_path = DATA_DIR / "venue_crm.csv"
    email_path = DRAFTS_DIR / "venue_outreach_email.md"
    _common.write_csv(crm_path, VENUE_CRM_COLUMNS, crm)
    email_path.write_text(_outreach_email(event))

    venues = event_state.setdefault("venues", {})
    venues["requirements"] = {
        "target_size": event.get("target_size") or 100,
        "format": "evening reception, ~3 hours",
        "needs": ["AV/mic", "outside food allowed", "load-in window", "wheelchair accessible"],
    }
    venues["pipeline"] = crm

    visibility.log_agent_run(
        agent_name="venue_agent",
        run_id=run_id,
        input_summary=f"{len(seeds)} venue candidates ({'seed' if files_read else 'sample'})",
        output_summary=f"venue_crm.csv ({len(crm)} rows) + venue_outreach_email.md",
        decisions_made=[
            "Standard 8-question venue intake (capacity, AV, food, load-in, insurance, floor plan)",
            "Default status = to_contact",
        ],
        reasoning_summary=(
            "We don't do live venue search in MVP; produce a CRM + a parametric outreach email "
            "the organizer can fire to known candidates."
        ),
        confidence="medium",
        files_read=files_read,
        files_written=[rel(crm_path), rel(email_path)],
        blockers=[],
        next_actions=[
            "Send venue_outreach_email.md to top 5 candidates",
            "Update venue_crm.csv as replies come in",
        ],
        event_state=event_state,
    )
    return {"candidates": len(crm)}
