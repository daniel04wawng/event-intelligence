"""Sponsor / Partner Ops Agent: lightweight ICP, CRM, outreach draft. No deck gen."""
from __future__ import annotations

from typing import Any

from packages.shared import visibility
from . import _common
from ._common import DATA_DIR, DRAFTS_DIR, rel

SPONSOR_CRM_COLUMNS = [
    "organization", "category", "poc_name", "poc_email", "warm_intro",
    "value_prop", "status", "last_touch", "next_step", "notes",
]

CATEGORIES = [
    "ai_infra_devtools",
    "startup_communities",
    "coworking_startup_spaces",
    "recruiting_talent",
    "cloud_data_platforms",
    "local_founder_communities",
]

SAMPLE_SPONSORS = [
    {"organization": "Modal", "category": "ai_infra_devtools"},
    {"organization": "LangChain", "category": "ai_infra_devtools"},
    {"organization": "South Park Commons", "category": "startup_communities"},
    {"organization": "AGI House", "category": "startup_communities"},
    {"organization": "Shack15", "category": "coworking_startup_spaces"},
    {"organization": "AWS Startups", "category": "cloud_data_platforms"},
]


def _outreach_msg(event: dict[str, Any], org: str) -> str:
    return (
        f"Hey [{org} contact], we're hosting a curated AI builders night in "
        f"{event.get('city') or 'SF'} for ~{event.get('target_size') or 100} founders/operators "
        f"in agent infra and devtools. Looking for a light partner — drinks/food sponsor or "
        f"co-host slot. Low lift, high alignment with your audience. Open to chatting?"
    )


def run(event_state: dict[str, Any]) -> dict[str, Any]:
    _common.ensure_dirs()
    run_id = visibility.create_run_id("sponsor_partner_agent")
    event = event_state.get("event", {}) or {}

    seeds = SAMPLE_SPONSORS
    crm: list[dict[str, Any]] = []
    for s in seeds:
        crm.append({
            "organization": s["organization"],
            "category": s["category"],
            "poc_name": "",
            "poc_email": "",
            "warm_intro": "",
            "value_prop": "co-host slot or food/drinks sponsor for curated AI builder night",
            "status": "to_contact",
            "last_touch": "",
            "next_step": "Find warm intro or send cold outreach",
            "notes": "",
        })

    crm_path = DATA_DIR / "sponsor_partner_crm.csv"
    msg_path = DRAFTS_DIR / "sponsor_partner_outreach.md"
    _common.write_csv(crm_path, SPONSOR_CRM_COLUMNS, crm)
    msg_path.write_text(
        "# Sponsor / Partner Outreach Drafts\n\n" +
        "\n\n".join(
            f"## {s['organization']} ({s['category']})\n\n{_outreach_msg(event, s['organization'])}"
            for s in seeds
        ) + "\n"
    )

    sponsors = event_state.setdefault("sponsors", {})
    sponsors["partner_icp"] = [{"category": c} for c in CATEGORIES]
    sponsors["pipeline"] = crm

    visibility.log_agent_run(
        agent_name="sponsor_partner_agent",
        run_id=run_id,
        input_summary=f"{len(CATEGORIES)} ICP categories",
        output_summary=f"sponsor_partner_crm.csv ({len(crm)} rows) + outreach drafts",
        decisions_made=["Lightweight: no deck, no tiers — single ask is co-host or food/drinks"],
        reasoning_summary=(
            "Partner economics for a 100-person event aren't worth heavy sponsor packaging. "
            "Produce a category list, sample CRM, and a one-paragraph ask."
        ),
        confidence="medium",
        files_read=[],
        files_written=[rel(crm_path), rel(msg_path)],
        blockers=[],
        next_actions=["Identify warm intros; replace sample list with real targets"],
        event_state=event_state,
    )
    return {"partners": len(crm)}
