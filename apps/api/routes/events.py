from fastapi import APIRouter

router = APIRouter(tags=["events"])

@router.post("/")
async def create_event():
    """Create a new event and kick off curation pipeline."""
    pass

@router.get("/{event_id}/shortlist")
async def get_shortlist(event_id: str):
    """Return ranked attendee shortlist for an event."""
    pass

@router.get("/{event_id}/sponsor-brief")
async def get_sponsor_brief(event_id: str):
    """Return sponsor-attendee alignment brief."""
    pass

@router.post("/{event_id}/attendees/upload")
async def upload_attendees(event_id: str):
    """Upload Luma/Partiful CSV post-event."""
    pass
