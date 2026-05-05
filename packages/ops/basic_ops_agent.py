"""Basic Ops Agent: minimum-viable event plan (checklist, run-of-show, timeline)."""
from __future__ import annotations

from typing import Any

from packages.shared import visibility
from . import _common
from ._common import DOCS_DIR, rel


def _checklist(target: int) -> str:
    snacks = max(target, 100)
    drinks = int(target * 2.5)
    staff = max(3, target // 35)
    return f"""# Basic Ops Checklist

## People
- {staff} staff/volunteers (check-in, host, floater)
- 1 organizer running the program

## Catering (estimates for {target} attendees)
- Light bites for ~{snacks} (assume some walk-ins, +10–20% buffer)
- ~{drinks} drinks total (mix beer / wine / N/A)

## Check-in
- Printed name list + name tags + sharpies
- 1–2 laptops/tablets for live RSVP lookup
- Clear signage from venue entrance

## AV
- Mic (1 wireless + 1 backup wired)
- Screen + HDMI + dongles
- Bluetooth speaker as fallback

## Day-of supplies
- Trash bags, paper towels, hand sanitizer
- Backup power strips + extension cords
- Sign-in QR poster + slack/discord QR

## Open risks
- Venue cancellation (have a backup confirmed by T-3d)
- Caterer delay (confirm load-in time T-1d)
- Day-of cancellations (over-invite per retention plan)
"""


RUN_OF_SHOW = """# Run of Show

- 5:00 PM — staff arrival, AV check, signage up
- 5:30 PM — caterer load-in, drinks chilled
- 6:00 PM — doors open, check-in begins, ambient music
- 6:20 PM — welcome from organizer (5 min)
- 6:30 PM — short structured intro / icebreaker activity (15 min)
- 6:45 PM — open networking, food + drinks
- 7:30 PM — optional 5-min spotlight from a guest builder
- 8:00 PM — soft close, last call
- 8:30 PM — teardown begins, venue cleared
- 9:00 PM — out
"""


def run(event_state: dict[str, Any]) -> dict[str, Any]:
    _common.ensure_dirs()
    run_id = visibility.create_run_id("basic_ops_agent")
    event = event_state.get("event", {}) or {}
    target = int(event.get("target_size") or 100)

    checklist_path = DOCS_DIR / "basic_ops_checklist.md"
    ros_path = DOCS_DIR / "run_of_show.md"
    checklist_path.write_text(_checklist(target))
    ros_path.write_text(RUN_OF_SHOW)

    event_state.setdefault("ops", {})["basic_ops_checklist"] = [
        {"area": "people", "status": "draft"},
        {"area": "catering", "status": "draft"},
        {"area": "check_in", "status": "draft"},
        {"area": "av", "status": "draft"},
        {"area": "supplies", "status": "draft"},
    ]

    visibility.log_agent_run(
        agent_name="basic_ops_agent",
        run_id=run_id,
        input_summary=f"target_size={target}",
        output_summary="basic_ops_checklist.md + run_of_show.md generated",
        decisions_made=[
            "Catering estimate uses 1.0x bites and 2.5x drinks per attendee",
            f"Staff sized at max(3, target/35) = {max(3, target//35)}",
        ],
        reasoning_summary=(
            "MVP-grade event production: enough to run a 100-person night without surprises, "
            "no full vendor sourcing or production schedule."
        ),
        confidence="medium",
        files_read=[],
        files_written=[rel(checklist_path), rel(ros_path)],
        blockers=[],
        next_actions=["Confirm caterer T-3d", "Walk venue T-1d"],
        event_state=event_state,
    )
    return {"target": target}
