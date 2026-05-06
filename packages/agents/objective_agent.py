"""Objective Agent — normalizes organizer input into a structured objective.

Pulls three pillars when possible (event type, desired attendees, overall goal)
via intent_extractor (LLM when configured, else labeled-section parsing), then
fills size/city with lightweight heuristics.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from packages.agents.intent_extractor import extract_event_intent
from packages.shared.visibility import create_run_id, log_agent_run


AGENT_NAME = "objective_agent"

# Baseline checklist merged into state / preview — surfaced until brief has answers.
DEFAULT_OPEN_QUESTIONS: list[str] = [
    "Is the event public or invite-only?",
    "Is there a sponsor or partner goal?",
    "Is the venue already secured?",
    "What is the exact date and time?",
    "Who is the primary host / face of the event?",
]


def _extract_int(text: str, default: int) -> int:
    m = re.search(r"(\d{2,4})\s*[- ]?\s*person", text, flags=re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(\d{2,4})\b", text)
    return int(m.group(1)) if m else default


def _extract_city(text: str) -> str:
    for token in ["SF", "San Francisco", "NYC", "New York", "LA", "Los Angeles", "Austin", "Seattle", "London"]:
        if re.search(rf"\b{re.escape(token)}\b", text, flags=re.IGNORECASE):
            return token
    return ""


def _extract_event_type(text: str) -> str:
    t = text.lower()
    if "hackathon" in t:
        return "hackathon"
    if "dinner" in t:
        return "curated dinner"
    if "panel" in t:
        return "panel"
    if "summit" in t or "conference" in t:
        return "summit"
    if "meetup" in t or "community" in t:
        return "curated tech community event"
    return "curated tech community event"


def _coerce_size(value: Any, brief: str, default: int) -> int:
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, float) and value > 0:
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return _extract_int(brief, default)


def run(brief: str, constraints: Optional[dict[str, Any]] = None,
        event_state: Optional[dict[str, Any]] = None,
        *,
        intent: Optional[dict[str, Any]] = None,
        persist_visibility: bool = True) -> dict[str, Any]:
    """Run the Objective Agent. Returns a structured objective dict.

    Pass ``intent`` when you already called ``extract_event_intent`` (e.g. preview UIs)
    to avoid duplicate LLM calls.
    """
    constraints = constraints or {}
    run_id = create_run_id(AGENT_NAME)

    intent = intent if intent is not None else extract_event_intent(brief)

    target_size = constraints.get("target_size") or _coerce_size(
        intent.get("target_size"), brief, 100
    )
    city = (constraints.get("city") or intent.get("city") or "").strip() or _extract_city(brief)

    event_type = (
        constraints.get("event_type")
        or (intent.get("event_type") or "").strip()
        or _extract_event_type(brief)
    )

    desired_attendees = (intent.get("desired_attendees") or "").strip()

    # Goal: structured intent first, then legacy heuristic on full brief
    goal = (intent.get("overall_goal") or "").strip()
    if not goal:
        m = re.search(r"goal[^.]*\.", brief, flags=re.IGNORECASE)
        if m:
            goal = m.group(0).strip()
        else:
            sentences = [s.strip() for s in re.split(r"[.\n]", brief) if s.strip()]
            if sentences:
                goal = max(sentences, key=len)

    event_name = (intent.get("event_name") or "").strip()

    success_metrics = [
        f"{target_size} RSVPs",
        f"{int(target_size * 0.6)}-{int(target_size * 0.7)} actual attendees",
        f"{max(20, int(target_size * 0.3))}+ high-fit attendees aligned with the theme",
        "10 meaningful post-event follow-ups",
    ]

    open_questions = list(DEFAULT_OPEN_QUESTIONS)

    objective = {
        "goal": goal,
        "event_type": event_type,
        "desired_attendees": desired_attendees,
        "target_size": target_size,
        "city": city,
        "success_metrics": success_metrics,
        "open_questions": open_questions,
        "event_name": event_name,
    }

    if event_state is not None:
        ev = event_state.setdefault("event", {})
        if event_name:
            ev["name"] = event_name
        ev["goal"] = goal
        ev["desired_attendees"] = desired_attendees
        ev["target_size"] = target_size
        ev["city"] = city
        ev["format"] = event_type
        ev["success_metrics"] = success_metrics
        state_meta = event_state.setdefault("state", {})
        state_meta.setdefault("open_questions", []).extend(open_questions)

    log_agent_run(
        AGENT_NAME,
        run_id=run_id,
        input_summary=f"Raw event brief ({len(brief)} chars)",
        output_summary=(
            f"Normalized {target_size}-person '{event_type}' in {city or 'unspecified city'}; "
            f"goal_len={len(goal)}, desired_attendees_len={len(desired_attendees)}."
        ),
        decisions_made=[
            f"event_type='{event_type}'.",
            f"target_size={target_size}, city='{city}'.",
            "Captured organizer triad: event type, desired attendees, overall goal (when extractable).",
        ],
        reasoning_summary=(
            "intent_extractor supplies event type, desired attendees, and overall goal when "
            "ANTHROPIC_API_KEY is set or when the brief uses labeled sections; size/city still "
            "use constraints, intent fields, and regex fallbacks on the full brief."
        ),
        confidence="medium",
        files_read=[],
        files_written=[],
        next_actions=["Run audience_agent to define ICP and avoid personas."],
        event_state=event_state,
        persist_to_disk=persist_visibility,
    )

    return objective
