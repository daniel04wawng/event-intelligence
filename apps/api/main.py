from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Event Intelligence API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

# Route registration (uncomment as you build)
# from apps.api.routes import events, sponsors, attendees, reports
# app.include_router(events.router, prefix="/events")
# app.include_router(sponsors.router, prefix="/sponsors")
# app.include_router(attendees.router, prefix="/attendees")
# app.include_router(reports.router, prefix="/reports")
