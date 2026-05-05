"""Rule-based, explainable attendee fit scoring.

Inputs: a person dict (per shared schema), audience ICP, scoring rubric, and
the event objective. Output is a dict with fit_score (0-100), priority bucket,
a human-readable reason, and tag list. No ML — every component of the score
is auditable and tweakable in audience_agent.py's rubric.
"""
from __future__ import annotations

from typing import Any


def _matches_signals(text: str, signals: list[str]) -> bool:
    if not signals:
        return False
    t = text.lower()
    return any(s.lower() in t for s in signals)


def _classify_persona(person: dict[str, Any], icp: list[dict], avoid: list[dict]) -> tuple[str | None, str | None]:
    """Returns (matched_icp_persona_name, matched_avoid_persona_name)."""
    haystack = " ".join(str(person.get(k, "")) for k in
                        ["role", "company", "why_relevant", "notes", "persona", "tags"])

    matched_icp = None
    # explicit persona override on the row wins
    for p in icp:
        if person.get("persona") == p["name"]:
            matched_icp = p["name"]
            break
    if not matched_icp:
        # score each persona by number of distinct signals that hit; tie-break on weight
        best: tuple[int, int, str] | None = None  # (hits, weight, name)
        h = haystack.lower()
        for p in icp:
            sigs = p.get("signals", []) or []
            hits = sum(1 for s in sigs if s.lower() in h)
            if hits == 0:
                continue
            cand = (hits, p.get("weight", 0), p["name"])
            if best is None or cand > best:
                best = cand
        if best is not None:
            matched_icp = best[2]

    matched_avoid = None
    for p in avoid:
        if _matches_signals(haystack, p.get("signals", [])):
            matched_avoid = p["name"]
            break

    return matched_icp, matched_avoid


def score(person: dict[str, Any],
          audience_icp: list[dict],
          scoring_rubric: dict[str, Any],
          objective: dict[str, Any],
          avoid_personas: list[dict] | None = None) -> dict[str, Any]:
    avoid_personas = avoid_personas or []
    weights: dict[str, int] = scoring_rubric.get("persona_weights", {})
    penalties: dict[str, int] = scoring_rubric.get("avoid_penalties", {})
    bonuses: dict[str, int] = scoring_rubric.get("bonuses", {})
    thresholds: dict[str, int] = scoring_rubric.get("thresholds", {"high": 75, "medium": 55, "low": 35})

    icp_match, avoid_match = _classify_persona(person, audience_icp, avoid_personas)

    components: list[tuple[str, int]] = []
    fit = 0

    if icp_match and icp_match in weights:
        fit += weights[icp_match]
        components.append((f"persona_match:{icp_match}", weights[icp_match]))

    text_blob = " ".join(str(person.get(k, "")) for k in
                         ["role", "why_relevant", "notes"]).lower()

    if any(s in text_blob for s in ["founder", "ceo", "cto", "head of", "lead"]):
        fit += bonuses.get("founder_or_lead_signal", 0)
        components.append(("founder_or_lead_signal", bonuses.get("founder_or_lead_signal", 0)))

    if person.get("linkedin_url") and any(s in text_blob for s in ["github", "writing", "blog", "open source", "oss"]):
        fit += bonuses.get("github_or_writing_signal", 0)
        components.append(("github_or_writing_signal", bonuses.get("github_or_writing_signal", 0)))

    if "warm" in text_blob or "intro" in text_blob:
        fit += bonuses.get("warm_intro", 0)
        components.append(("warm_intro", bonuses.get("warm_intro", 0)))

    obj_city = (objective.get("city") or "").lower()
    if obj_city and obj_city in text_blob:
        fit += bonuses.get("city_match", 0)
        components.append(("city_match", bonuses.get("city_match", 0)))

    if avoid_match and avoid_match in penalties:
        fit -= penalties[avoid_match]
        components.append((f"avoid_penalty:{avoid_match}", -penalties[avoid_match]))

    fit = max(0, min(100, fit))

    if avoid_match:
        priority = "needs_review"
    elif fit >= thresholds.get("high", 75):
        priority = "high"
    elif fit >= thresholds.get("medium", 55):
        priority = "medium"
    elif fit >= thresholds.get("low", 35):
        priority = "low"
    else:
        priority = "needs_review"

    reason_parts = []
    if icp_match:
        reason_parts.append(f"Matches ICP persona '{icp_match}'.")
    else:
        reason_parts.append("No clear ICP persona match from available fields.")
    if avoid_match:
        reason_parts.append(f"Flagged for avoid persona '{avoid_match}'.")
    if components:
        breakdown = ", ".join(f"{name}({pts:+d})" for name, pts in components)
        reason_parts.append(f"Score breakdown: {breakdown}.")

    tags = []
    if icp_match:
        tags.append(icp_match)
    if avoid_match:
        tags.append(f"avoid:{avoid_match}")

    return {
        "fit_score": fit,
        "priority": priority,
        "reason": " ".join(reason_parts),
        "tags": tags,
    }


def score_all(people: list[dict[str, Any]],
              audience_icp: list[dict],
              scoring_rubric: dict[str, Any],
              objective: dict[str, Any],
              avoid_personas: list[dict] | None = None) -> list[dict[str, Any]]:
    """Annotate each person in-place with fit_score / priority / why_relevant; return ranked list."""
    out = []
    for p in people:
        s = score(p, audience_icp, scoring_rubric, objective, avoid_personas)
        p["fit_score"] = s["fit_score"]
        p["priority"] = s["priority"]
        if not p.get("why_relevant"):
            p["why_relevant"] = s["reason"]
        existing_tags = p.get("tags") or []
        if isinstance(existing_tags, str):
            existing_tags = [existing_tags]
        p["tags"] = list({*existing_tags, *s["tags"]})
        if not p.get("persona") and s["tags"]:
            p["persona"] = next((t for t in s["tags"] if not t.startswith("avoid:")), "")
        out.append(p)
    out.sort(key=lambda x: (x.get("fit_score") or 0), reverse=True)
    return out
