"""High-level DB write helpers used by the pipeline.

Designed so agents call these without depending on SQLAlchemy specifics. All
writes are best-effort — if `DATABASE_URL` is unset or the DB is unreachable,
helpers return None and the file-based outputs still work. The pipeline never
fails because of a DB issue.
"""
from __future__ import annotations

import os
from typing import Any
from uuid import UUID, uuid4

# Make apps/api importable as a top-level package
import sys
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _try_import_db():
    """Lazily import the DB stack so the pipeline doesn't choke on a missing
    SQLAlchemy install in offline mode."""
    try:
        from apps.api.db.session import db_available, session_scope  # type: ignore
        from apps.api.db.models import Event, Person, AgentRun  # type: ignore
        from sqlalchemy.dialects.postgresql import insert as pg_insert  # type: ignore
        from sqlalchemy import select  # type: ignore
        return {
            "db_available": db_available,
            "session_scope": session_scope,
            "Event": Event,
            "Person": Person,
            "AgentRun": AgentRun,
            "pg_insert": pg_insert,
            "select": select,
        }
    except Exception:
        return None


def is_db_enabled() -> bool:
    if not os.environ.get("DATABASE_URL"):
        return False
    return _try_import_db() is not None


def upsert_event(event_state: dict[str, Any], brief_text: str = "") -> UUID | None:
    """Upsert an event row from event_state. Matches by `name`. Returns event_id."""
    db = _try_import_db()
    if not db or not db["db_available"]():
        return None

    Event = db["Event"]
    select = db["select"]

    ev = event_state.get("event", {}) or {}
    name = ev.get("name") or "Untitled Event"

    with db["session_scope"]() as s:
        existing = s.execute(select(Event).where(Event.name == name)).scalar_one_or_none()
        if existing is None:
            row = Event(
                name=name,
                goal=ev.get("goal") or None,
                city=ev.get("city") or None,
                target_size=ev.get("target_size"),
                format=ev.get("format") or None,
                brief_text=brief_text or None,
                success_metrics=ev.get("success_metrics") or [],
                intelligence=event_state.get("intelligence") or {},
                state=event_state.get("state") or {},
                visibility=event_state.get("visibility") or {},
            )
            s.add(row)
            s.flush()
            return row.id
        # update fields
        existing.goal = ev.get("goal") or existing.goal
        existing.city = ev.get("city") or existing.city
        existing.target_size = ev.get("target_size") or existing.target_size
        existing.format = ev.get("format") or existing.format
        existing.brief_text = brief_text or existing.brief_text
        existing.success_metrics = ev.get("success_metrics") or existing.success_metrics
        existing.intelligence = event_state.get("intelligence") or existing.intelligence
        existing.state = event_state.get("state") or existing.state
        existing.visibility = event_state.get("visibility") or existing.visibility
        return existing.id


def upsert_people(event_id: UUID, people: list[dict[str, Any]]) -> int:
    """Upsert ranked people for an event. Idempotent — re-runs UPSERT same person.

    Conflict resolution: prefers (event_id, linkedin_url) when linkedin_url is
    present and non-empty, else (event_id, name, company).
    Returns the number of rows touched.
    """
    db = _try_import_db()
    if not db or not db["db_available"]() or not people:
        return 0

    Person = db["Person"]
    select = db["select"]

    touched = 0
    with db["session_scope"]() as s:
        for p in people:
            name = (p.get("name") or "").strip()
            if not name:
                continue
            company = (p.get("company") or "").strip() or None
            linkedin = (p.get("linkedin_url") or "").strip() or None

            stmt = select(Person).where(Person.event_id == event_id, Person.name == name)
            if company is not None:
                stmt = stmt.where(Person.company == company)
            existing = s.execute(stmt).scalars().first()

            if existing is None and linkedin:
                # second-chance match by linkedin url
                stmt2 = select(Person).where(
                    Person.event_id == event_id, Person.linkedin_url == linkedin
                )
                existing = s.execute(stmt2).scalars().first()

            payload = dict(
                event_id=event_id,
                name=name,
                company=company,
                role=p.get("role") or None,
                linkedin_url=linkedin,
                email=p.get("email") or None,
                persona=p.get("persona") or None,
                fit_score=p.get("fit_score"),
                priority=p.get("priority") or None,
                why_relevant=p.get("why_relevant") or None,
                tags=_coerce_tags(p.get("tags")),
                status=p.get("status") or "not_contacted",
                source=p.get("source") or None,
                outreach_angle=p.get("outreach_angle") or None,
                notes=p.get("notes") or None,
                raw=_coerce_raw(p),
            )
            if existing is None:
                s.add(Person(**payload))
            else:
                for k, v in payload.items():
                    if k == "event_id":
                        continue
                    setattr(existing, k, v)
            touched += 1
    return touched


def append_agent_run(entry: dict[str, Any], event_id: UUID | None = None) -> bool:
    """Append a visibility-trace entry to agent_runs. Returns True on success."""
    db = _try_import_db()
    if not db or not db["db_available"]():
        return False
    AgentRun = db["AgentRun"]
    try:
        with db["session_scope"]() as s:
            row = AgentRun(
                run_id=entry.get("run_id") or "",
                event_id=event_id,
                branch_context=entry.get("branch_context") or "event_intelligence",
                agent_name=entry.get("agent_name") or "",
                input_summary=entry.get("input_summary"),
                output_summary=entry.get("output_summary"),
                decisions_made=entry.get("decisions_made") or [],
                reasoning_summary=entry.get("reasoning_summary"),
                confidence=str(entry.get("confidence")) if entry.get("confidence") is not None else None,
                files_read=list(entry.get("files_read") or []),
                files_written=list(entry.get("files_written") or []),
                blockers=entry.get("blockers") or [],
                next_actions=entry.get("next_actions") or [],
            )
            s.add(row)
        return True
    except Exception:
        return False


# ---------- helpers ----------

def _coerce_tags(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        # CSV-loaded tags often arrive as JSON-encoded strings
        if v.startswith("[") and v.endswith("]"):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except json.JSONDecodeError:
                pass
        return [v] if v else []
    if isinstance(v, list):
        return [str(x) for x in v]
    return []


def _coerce_raw(p: dict[str, Any]) -> dict[str, Any]:
    """Anything non-canonical goes into the `raw` JSONB bucket."""
    canonical = {
        "name", "company", "role", "linkedin_url", "email", "persona",
        "fit_score", "priority", "why_relevant", "tags", "status",
        "source", "outreach_angle", "notes",
    }
    return {k: v for k, v in p.items() if k not in canonical}
