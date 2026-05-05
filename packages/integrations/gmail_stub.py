"""Stub: would create Gmail drafts from outreach_queue.csv. Writes local .eml-style files."""
from __future__ import annotations

import csv
import re
from pathlib import Path


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "draft"


def create_email_drafts_stub(outreach_queue_path: str | Path, drafts_dir: str | Path = "drafts/emails") -> dict:
    qp = Path(outreach_queue_path)
    out_dir = Path(drafts_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    if not qp.exists():
        print(f"[gmail_stub] no queue at {qp}")
        return {"written": 0, "stub": True}
    with qp.open() as f:
        for row in csv.DictReader(f):
            if (row.get("channel") or "").lower() != "email":
                continue
            fname = out_dir / f"{_slug(row.get('name'))}-{_slug(row.get('company'))}.md"
            fname.write_text(
                f"To: {row.get('name','')}\nPriority: {row.get('priority','')}\n\n{row.get('message','')}\n\n"
                f"---\nFollow-up: {row.get('follow_up_message','')}\n"
            )
            written += 1
    print(f"[gmail_stub] would create {written} Gmail drafts (saved locally to {out_dir})")
    return {"written": written, "drafts_dir": str(out_dir), "stub": True}
