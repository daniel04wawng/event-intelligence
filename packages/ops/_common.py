"""Shared helpers for ops agents: paths, csv io, branch context."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from packages.shared import visibility

BRANCH_CONTEXT = "agentic_ops"
visibility.set_branch_context(BRANCH_CONTEXT)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
DOCS_DIR = REPO_ROOT / "docs"
DRAFTS_DIR = REPO_ROOT / "drafts"
LOGS_DIR = REPO_ROOT / "logs"

EVENT_STATE_PATH = DATA_DIR / "event_state.json"
RANKED_PEOPLE_PATH = DATA_DIR / "ranked_people.csv"
INTELLIGENCE_SUMMARY_PATH = DOCS_DIR / "intelligence_summary.md"


def ensure_dirs() -> None:
    for d in (DATA_DIR, DOCS_DIR, DRAFTS_DIR, LOGS_DIR, DRAFTS_DIR / "emails"):
        d.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, columns: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: _csv_value(row.get(c, "")) for c in columns})


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", newline="") as f:
        return list(csv.DictReader(f))


def _csv_value(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def rel(path: Path) -> str:
    """Path relative to repo root, for logging."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
