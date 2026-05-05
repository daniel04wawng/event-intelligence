"""Audience Intelligence Agent.

Produces ICP personas, avoid personas, approval criteria, data-to-collect, and
sourcing channels. Rule-based MVP keyed off the inferred event_type and goal
keywords. Designed so the scoring rubric it emits is consumed unchanged by
packages/scoring/attendee_fit.py.
"""
from __future__ import annotations

from typing import Any, Optional

from packages.shared.visibility import create_run_id, log_agent_run


AGENT_NAME = "audience_agent"


# Theme-keyed persona libraries. Order matters: higher-weight personas first.
_AI_BUILDER_PERSONAS = [
    {
        "name": "ai_agent_founder",
        "description": "Founders building AI agent products or agent infrastructure.",
        "weight": 10,
        "signals": ["founder", "ceo", "co-founder", "cofounder"],
    },
    {
        "name": "ai_infra_builder",
        "description": "Engineers building AI infra, devtools, or agent frameworks.",
        "weight": 9,
        "signals": ["infra", "platform", "devtools", "framework", "ai engineer",
                    "staff engineer", "ml engineer", "principal engineer"],
    },
    {
        "name": "technical_operator",
        "description": "Technical PMs, applied AI leads, or hands-on operators shipping AI products.",
        "weight": 7,
        "signals": ["applied ai", "ml lead", "head of ai", "head of ml",
                    "technical pm", "product manager", "applied scientist"],
    },
    {
        "name": "community_connector",
        "description": "High-signal community organizers, prolific writers, or hub people.",
        "weight": 6,
        "signals": ["community", "organizer", "writer", "researcher", "scout", "podcast"],
    },
    {
        "name": "investor_high_signal",
        "description": "Investors only if they materially improve room quality (partners at top funds, ex-operators).",
        "weight": 4,
        "signals": ["partner", "principal", "general partner", "gp", "venture"],
    },
]

_AI_BUILDER_AVOID = [
    {
        "name": "generic_networker",
        "description": "Attending purely to network with no clear connection to the theme.",
        "penalty": 15,
        "signals": ["bd", "business development", "sales rep"],
    },
    {
        "name": "sales_only",
        "description": "Sales-only attendees with no technical or product context.",
        "penalty": 12,
        "signals": ["account executive", "sdr", "ae", "enterprise sales"],
    },
    {
        "name": "low_context",
        "description": "Attendees with no clear connection to AI/agent infra theme.",
        "penalty": 10,
        "signals": [],
    },
    {
        "name": "free_food_only",
        "description": "Showing up for the perks rather than the conversation.",
        "penalty": 8,
        "signals": [],
    },
]


def _select_personas(event_type: str, goal: str) -> tuple[list[dict], list[dict]]:
    text = f"{event_type} {goal}".lower()
    if any(k in text for k in ["ai", "agent", "llm", "infra", "builder"]):
        return _AI_BUILDER_PERSONAS, _AI_BUILDER_AVOID
    # default fallback uses the same library
    return _AI_BUILDER_PERSONAS, _AI_BUILDER_AVOID


def run(objective: dict[str, Any],
        event_state: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    run_id = create_run_id(AGENT_NAME)
    event_type = objective.get("event_type", "")
    goal = objective.get("goal", "")
    city = objective.get("city", "")

    icp, avoid = _select_personas(event_type, goal)

    approval_criteria = [
        "Clear connection to the event theme (AI / agent infra / builders).",
        "Currently building, leading, or deeply operating in a relevant role.",
        "Likely to contribute to the room (not just consume).",
        "Not flagged as an avoid persona.",
    ]

    data_to_collect = [
        "name", "company", "role", "linkedin_url", "email",
        "github_username", "twitter_handle",
        "what they're currently building", "why they want to attend",
        "introductions they're hoping to make",
    ]

    sourcing_channels = [
        {"channel": "Luma attendee lists from similar events", "priority": "high"},
        {"channel": "Founder/builder Twitter (X) lists", "priority": "high"},
        {"channel": "GitHub contributors to relevant agent/infra repos", "priority": "high"},
        {"channel": "Personal/team networks (warm intros)", "priority": "high"},
        {"channel": "AI infra Slack/Discord communities", "priority": "medium"},
        {"channel": "YC and top-fund portfolio lists (relevant tracks only)", "priority": "medium"},
    ]

    scoring_rubric = {
        "max_score": 100,
        "persona_weights": {p["name"]: p["weight"] * 8 for p in icp},  # base contribution
        "avoid_penalties": {p["name"]: p["penalty"] for p in avoid},
        "bonuses": {
            "city_match": 10,
            "founder_or_lead_signal": 8,
            "github_or_writing_signal": 6,
            "warm_intro": 6,
        },
        "thresholds": {
            "high": 75,
            "medium": 55,
            "low": 35,
        },
        "notes": "Rule-based and explainable. See packages/scoring/attendee_fit.py.",
    }

    out = {
        "audience_icp": icp,
        "avoid_personas": avoid,
        "approval_criteria": approval_criteria,
        "data_to_collect": data_to_collect,
        "sourcing_channels": sourcing_channels,
        "scoring_rubric": scoring_rubric,
    }

    if event_state is not None:
        intel = event_state.setdefault("intelligence", {})
        intel["audience_icp"] = icp
        intel["avoid_personas"] = avoid
        intel["scoring_rubric"] = scoring_rubric
        intel.setdefault("notes", []).append(
            f"Approval criteria: {len(approval_criteria)} items. Sourcing channels: {len(sourcing_channels)}."
        )

    log_agent_run(
        AGENT_NAME,
        run_id=run_id,
        input_summary=f"Objective for '{event_type}' in {city or 'unspecified city'}.",
        output_summary=f"Defined {len(icp)} ICP personas and {len(avoid)} avoid personas; emitted scoring rubric.",
        decisions_made=[
            f"Selected AI-builder persona library based on goal/event_type keywords.",
            f"Set high-fit threshold to {scoring_rubric['thresholds']['high']}.",
        ],
        reasoning_summary=(
            "Personas are weighted by likely contribution to room quality. Avoid personas reflect "
            "the highest-frequency negative signals at curated AI events: generic networkers and "
            "sales-only attendees. The rubric is rule-based so scores are auditable."
        ),
        confidence="medium",
        next_actions=["Run sourcing_agent to define queries and ingest seed CSV."],
        event_state=event_state,
    )

    return out
