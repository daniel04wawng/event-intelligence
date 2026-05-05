"""Stub: would sync a CSV to a Google Sheet. No real auth, prints intent."""
from __future__ import annotations

from pathlib import Path


def write_csv_to_sheet_stub(csv_path: str | Path, sheet_name: str) -> dict:
    p = Path(csv_path)
    rows = sum(1 for _ in p.open()) - 1 if p.exists() else 0
    msg = f"[google_sheets_stub] would sync {p} ({rows} rows) -> sheet '{sheet_name}'"
    print(msg)
    return {"csv_path": str(p), "sheet_name": sheet_name, "rows": rows, "synced": False, "stub": True}
