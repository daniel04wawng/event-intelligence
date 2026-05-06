"""POST /run — thin HTTP adapter over ``packages.agents.run_intelligence.run_pipeline``.

Keeps orchestration in ``packages/``; the API only validates input and runs sync work
in a threadpool so the event loop stays responsive.
"""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

router = APIRouter(tags=["pipeline"])


class PipelineRunRequest(BaseModel):
    brief_text: str = Field(..., min_length=1, description="Full organizer brief / proposal text.")
    seed_csv_path: Optional[str] = Field(
        None,
        description="Optional path to seed CSV relative to process cwd (e.g. data/people_seed.csv).",
    )


def _validate_seed_path(raw: Optional[str]) -> Optional[str]:
    if raw is None or not raw.strip():
        return None
    p = Path(raw)
    if p.is_absolute():
        raise HTTPException(status_code=400, detail="seed_csv_path must be a relative path.")
    if ".." in p.parts:
        raise HTTPException(status_code=400, detail="seed_csv_path cannot contain '..'.")
    if not p.exists():
        raise HTTPException(status_code=400, detail=f"seed_csv_path not found: {raw}")
    return str(p)


@router.post("/run")
async def run_pipeline_http(body: PipelineRunRequest) -> dict:
    seed = _validate_seed_path(body.seed_csv_path)

    def _execute():
        from packages.agents.run_intelligence import run_pipeline

        return run_pipeline(
            body.brief_text,
            seed_csv_path=seed,
            brief_source_label="POST /run",
            quiet=True,
        )

    try:
        code, summary = await run_in_threadpool(_execute)
    except Exception as e:
        msg = str(e) or repr(e)
        low = msg.lower()
        if "credit balance is too low" in low:
            msg = ("Anthropic account is out of credits. Top up at "
                   "https://console.anthropic.com/settings/billing then retry.")
        elif "invalid x-api-key" in low or "authentication_error" in low:
            msg = "ANTHROPIC_API_KEY is invalid or revoked. Update .env and restart the server."
        raise HTTPException(status_code=502, detail=msg)
    if code != 0:
        raise HTTPException(status_code=400, detail=summary.get("error", "pipeline_failed"))
    return {"ok": True, **summary}
