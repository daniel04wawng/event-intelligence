"""Reply Tracker: ingest data/replies.csv, update guest CRM / outreach queue / retention tracker / event_state."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from packages.shared import visibility
from packages.shared.event_state import load_event_state, save_event_state
from . import _common
from ._common import DATA_DIR, EVENT_STATE_PATH, rel
from .outreach_agent import GUEST_CRM_COLUMNS, OUTREACH_COLUMNS
from .retention_agent import RETENTION_COLUMNS


def run(replies_path=None) -> dict[str, Any]:
    _common.ensure_dirs()
    run_id = visibility.create_run_id("reply_tracker")
    replies_path = replies_path or (DATA_DIR / "replies.csv")
    replies = _common.read_csv(replies_path)
    if not replies:
        return {"updated": 0, "note": "no replies.csv found"}

    event_state = load_event_state(EVENT_STATE_PATH)
    now = datetime.now(timezone.utc).isoformat()

    by_name = {(r.get("name") or "").lower(): r for r in replies}

    def _apply(rows: list[dict], status_field: str) -> int:
        n = 0
        for row in rows:
            r = by_name.get((row.get("name") or "").lower())
            if not r:
                continue
            row[status_field] = r.get("reply_status", row.get(status_field, ""))
            row["last_touch"] = now
            if r.get("notes"):
                row["notes"] = (row.get("notes", "") + " | " + r["notes"]).strip(" |")
            n += 1
        return n

    crm = _common.read_csv(DATA_DIR / "guest_crm.csv")
    queue = _common.read_csv(DATA_DIR / "outreach_queue.csv")
    tracker = _common.read_csv(DATA_DIR / "retention_tracker.csv")

    updated_crm = _apply(crm, "rsvp_status")
    updated_queue = _apply(queue, "status")
    updated_tracker = _apply(tracker, "rsvp_status")

    if crm:
        _common.write_csv(DATA_DIR / "guest_crm.csv", GUEST_CRM_COLUMNS, crm)
    if queue:
        _common.write_csv(DATA_DIR / "outreach_queue.csv", OUTREACH_COLUMNS, queue)
    if tracker:
        _common.write_csv(DATA_DIR / "retention_tracker.csv", RETENTION_COLUMNS, tracker)

    visibility.log_agent_run(
        agent_name="reply_tracker",
        run_id=run_id,
        input_summary=f"{len(replies)} replies",
        output_summary=f"updated guest_crm={updated_crm}, queue={updated_queue}, tracker={updated_tracker}",
        decisions_made=["Match by lowercased name; last_touch timestamp updated on match"],
        reasoning_summary="Reply ingestion is the heartbeat of RSVP/retention; this is the MVP file-based version.",
        confidence="high",
        files_read=[rel(replies_path)],
        files_written=[
            rel(DATA_DIR / "guest_crm.csv"),
            rel(DATA_DIR / "outreach_queue.csv"),
            rel(DATA_DIR / "retention_tracker.csv"),
        ],
        blockers=[],
        next_actions=["Re-run retention_agent to recompute RSVP math"],
        event_state=event_state,
    )
    save_event_state(EVENT_STATE_PATH, event_state)
    return {"updated_crm": updated_crm, "updated_queue": updated_queue, "updated_tracker": updated_tracker}


if __name__ == "__main__":
    print(run())
