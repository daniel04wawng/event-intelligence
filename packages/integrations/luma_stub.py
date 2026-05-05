"""Stub: would create a Luma event page. Writes a local markdown draft."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def create_luma_event_copy_stub(event_state: dict[str, Any],
                                out_path: str | Path = "drafts/luma_event_page.md") -> dict:
    event = event_state.get("event", {}) or {}
    name = event.get("name") or "AI Builders Night"
    city = event.get("city") or "SF"
    date = event.get("date") or "TBD"
    target = event.get("target_size") or 100
    goal = event.get("goal") or "build community around agent infrastructure and devtools"

    body = f"""# {name}

**City:** {city}  **Date:** {date}  **Capacity:** {target}

## What this is
A small, curated evening for founders and operators working on agent infrastructure,
devtools, and the AI builder stack. Light program + structured networking.

## Why come
- Goal: {goal}
- Quality of room over quantity — request-to-attend
- Light bites + drinks

## Format
- 6:00 PM doors
- 6:30 PM short program
- Open networking until 8:30 PM

Apply to attend. We'll review and confirm within 48 hours.
"""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    print(f"[luma_stub] would create Luma event page (saved to {p})")
    return {"out_path": str(p), "stub": True}
