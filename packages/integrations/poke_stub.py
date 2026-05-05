"""Stub: would queue Poke (LinkedIn-style) messages. Writes a local CSV."""
from __future__ import annotations

import csv
from pathlib import Path


def create_poke_message_queue_stub(outreach_queue_path: str | Path,
                                   out_path: str | Path = "drafts/poke_messages.csv") -> dict:
    qp = Path(outreach_queue_path)
    op = Path(out_path)
    op.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    if qp.exists():
        with qp.open() as f:
            for row in csv.DictReader(f):
                if (row.get("channel") or "").lower() in {"linkedin", "poke"}:
                    rows.append({
                        "name": row.get("name", ""),
                        "channel": row.get("channel", ""),
                        "priority": row.get("priority", ""),
                        "message": row.get("message", ""),
                        "follow_up": row.get("follow_up_message", ""),
                    })
    with op.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "channel", "priority", "message", "follow_up"])
        w.writeheader()
        w.writerows(rows)
    print(f"[poke_stub] would queue {len(rows)} Poke/LinkedIn messages (saved to {op})")
    return {"queued": len(rows), "out_path": str(op), "stub": True}
