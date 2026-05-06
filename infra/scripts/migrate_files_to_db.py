"""One-shot migrator: reads data/event_state.json + data/ranked_people.csv +
logs/agent_runs.jsonl from the local repo and writes them to Postgres.

Run after applying infra/scripts/init_db.sql once. Idempotent — safe to re-run.

Usage:
    export DATABASE_URL=postgresql://...
    python -m infra.scripts.migrate_files_to_db
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from packages.shared import db as _db  # noqa: E402

EVENT_STATE = REPO_ROOT / "data" / "event_state.json"
RANKED_CSV = REPO_ROOT / "data" / "ranked_people.csv"
RUNS_JSONL = REPO_ROOT / "logs" / "agent_runs.jsonl"


def main() -> int:
    if not _db.is_db_enabled():
        print("ERROR: DATABASE_URL is not set or DB stack not importable.", file=sys.stderr)
        return 2

    if not EVENT_STATE.exists():
        print(f"ERROR: missing {EVENT_STATE}", file=sys.stderr)
        return 2

    state = json.loads(EVENT_STATE.read_text())

    brief_path = REPO_ROOT / "data" / "event_brief.txt"
    brief = brief_path.read_text() if brief_path.exists() else ""

    print("Upserting event…")
    event_id = _db.upsert_event(state, brief_text=brief)
    print(f"  event_id = {event_id}")

    if RANKED_CSV.exists():
        with RANKED_CSV.open() as f:
            people = list(csv.DictReader(f))
        # convert numeric / list fields back from CSV strings
        for p in people:
            try:
                p["fit_score"] = int(p["fit_score"]) if p.get("fit_score") not in (None, "") else None
            except ValueError:
                p["fit_score"] = None
        print(f"Upserting {len(people)} people…")
        rows = _db.upsert_people(event_id, people)
        print(f"  rows touched = {rows}")
    else:
        print("(no ranked_people.csv to import)")

    if RUNS_JSONL.exists():
        count = 0
        with RUNS_JSONL.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ok = _db.append_agent_run(entry, event_id=event_id)
                if ok:
                    count += 1
        print(f"Appended {count} agent_runs.")
    else:
        print("(no agent_runs.jsonl to import)")

    print("Migration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
