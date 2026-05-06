"""
Pipeline route — /run
---------------------
Accepts a POST request with an event brief and an optional seed CSV path,
validates the input, then runs the intelligence pipeline in a threadpool
executor so the async event loop is never blocked.
"""
from __future__ import annotations

import asyncio
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from packages.agents.run_intelligence import run_pipeline

router = APIRouter(tags=["pipeline"])


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class PipelineRunRequest(BaseModel):
    brief_text: str
    seed_csv_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_seed_path(path: str) -> None:
    """Raise HTTPException(400) if *path* is unsafe or does not exist.

    Rules enforced:
    - Must be a relative path (no leading ``/`` or drive letter).
    - Must not contain ``..`` path components.
    - The resolved file must exist on disk.
    """
    if os.path.isabs(path):
        raise HTTPException(
            status_code=400,
            detail="seed_csv_path must be a relative path, not an absolute one.",
        )

    # Normalise and check for directory traversal
    normalised = os.path.normpath(path)
    parts = normalised.replace("\\", "/").split("/")
    if ".." in parts:
        raise HTTPException(
            status_code=400,
            detail='seed_csv_path must not contain ".." components.',
        )

    if not os.path.exists(normalised):
        raise HTTPException(
            status_code=400,
            detail=f"seed_csv_path does not exist: {normalised!r}",
        )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/run")
async def run(request: PipelineRunRequest):
    """Trigger the event intelligence pipeline.

    - Validates ``seed_csv_path`` when provided.
    - Runs the synchronous ``run_pipeline()`` in a threadpool so the
      async event loop stays responsive.
    - Returns ``{"ok": True, ...summary}`` on success.
    - Returns a descriptive ``HTTPException`` on Anthropic auth/credit
      errors or any other failure.
    """
    if request.seed_csv_path is not None:
        _validate_seed_path(request.seed_csv_path)

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            run_pipeline,
            request.brief_text,
            request.seed_csv_path,
        )
    except Exception as exc:  # noqa: BLE001
        _handle_pipeline_error(exc)

    return {"ok": True, **result}


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def _handle_pipeline_error(exc: Exception) -> None:
    """Translate known pipeline exceptions into HTTP responses.

    Raises an ``HTTPException`` in all cases so the caller always gets a
    structured JSON error body.
    """
    exc_str = str(exc)
    exc_type = type(exc).__name__

    # Anthropic credit exhaustion
    if "credit" in exc_str.lower() or "balance" in exc_str.lower():
        raise HTTPException(
            status_code=402,
            detail=(
                "Anthropic API credit balance is insufficient to complete the "
                "request.  Please top up your Anthropic account and retry."
            ),
        )

    # Anthropic authentication failure
    if (
        "invalid" in exc_str.lower() and "key" in exc_str.lower()
    ) or "authentication" in exc_str.lower() or "AuthenticationError" in exc_type:
        raise HTTPException(
            status_code=401,
            detail=(
                "Anthropic API key is invalid or missing.  Set a valid "
                "ANTHROPIC_API_KEY environment variable and restart the server."
            ),
        )

    # Generic / unexpected error — surface the message without leaking a
    # full traceback to the client.
    raise HTTPException(
        status_code=500,
        detail=f"Pipeline error ({exc_type}): {exc_str}",
    )
