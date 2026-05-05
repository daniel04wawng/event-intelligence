"""Objective Agent — normalizes a raw event brief into a structured objective.

This is a deterministic, rule-based MVP. Future versions can swap in an LLM
call without changing the public interface.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from packages.shared.visibility import create_run_id, log_agent_run


AGENT_NAME = "objective_agent"


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


def run(brief: str, constraints: Optional[dict[str, Any]] = None,
        event_state: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Run the Objective Agent. Returns a structured objective dict."""
    constraints = constraints or {}
    run_id = create_run_id(AGENT_NAME)

    target_size = constraints.get("target_size") or _extract_int(brief, 100)
    city = constraints.get("city") or _extract_city(brief)
    event_type = constraints.get("event_type") or _extract_event_type(brief)

    # derive a goal sentence: first sentence with "goal" if present, else summary line
    goal = ""
    m = re.search(r"goal[^.]*\.", brief, flags=re.IGNORECASE)
    if m:
        goal = m.group(0).strip()
    else:
        # fall back to the longest sentence
        sentences = [s.strip() for s in re.split(r"[.\n]", brief) if s.strip()]
        if sentences:
            goal = max(sentences, key=len)

    success_metrics = [
        f"{target_size} RSVPs",
        f"{int(target_size * 0.6)}-{int(target_size * 0.7)} actual attendees",
        f"{max(20, int(target_size * 0.3))}+ high-fit attendees aligned with the theme",
        "10 meaningful post-event follow-ups",
    ]

    open_questions = [
        "Is the event public or invite-only?",
        "Is there a sponsor or partner goal?",
        "Is the venue already secured?",
        "What is the exact date and time?",
        "Who is the primary host / face of the event?",
    ]

    objective = {
        "goal": goal,
        "event_type": event_type,
        "target_size": target_size,
        "city": city,
        "success_metrics": success_metrics,
        "open_questions": open_questions,
    }

    if event_state is not None:
        ev = event_state.setdefault("event", {})
        ev["goal"] = goal
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
        output_summary=f"Normalized objective for a {target_size}-person {event_type} in {city or 'unspecified city'}.",
        decisions_made=[
            f"Inferred event_type='{event_type}' from brief keywords.",
            f"Inferred target_size={target_size}.",
            f"Inferred city='{city}'.",
        ],
        reasoning_summary=(
            "Used keyword matching over the brief to infer event size, city, and event type. "
            "Goal sentence is the first sentence containing 'goal' or the longest sentence as fallback."
        ),
        confidence="medium",
        files_read=[],
        files_written=[],
        next_actions=["Run audience_agent to define ICP and avoid personas."],
        event_state=event_state,
    )

    return objective
