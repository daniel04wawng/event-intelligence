from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict

from packages.agents.run_intelligence import run_pipeline

router = APIRouter(tags=["pipeline"])


class PipelineRunRequest(BaseModel):
    event_id: str
    stage: str
    payload: Dict[str, Any] = {}


@router.post("/run")
async def run(request: PipelineRunRequest):
    """Trigger the intelligence pipeline for a given event and stage."""
    result = await run_pipeline(request.model_dump())
    return {"status": "ok", "result": result}
