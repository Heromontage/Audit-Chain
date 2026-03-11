"""
AuditChain — FastAPI Route Definitions

Four endpoints mounted under ``/api/v1``:

    POST   /audit                    — launch a new audit session
    GET    /audit/{session_id}/trail  — fetch on-chain audit trail
    GET    /audit/{session_id}/report — fetch the final report
    GET    /health                    — service + WeilChain health
"""

from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from agent.graph import run_audit
from api.schemas import (
    AuditRequest,
    AuditResponse,
    AuditTrailResponse,
    HealthResponse,
)
from weilchain.audit_client import audit_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["AuditChain"])

# ── POST /audit ──────────────────────────────────────────────────────────


@router.post("/audit", response_model=AuditResponse)
async def create_audit(request: AuditRequest) -> AuditResponse:
    """Launch a new Web3 due-diligence audit session.

    Generates a unique ``session_id``, runs the full LangGraph agent
    loop, and returns the structured report together with every
    WeilChain ``tx_hash`` as immutable on-chain proof.
    """
    session_id = str(uuid4())
    query = request.query

    # Enrich the query with the target address when supplied
    if request.target_address:
        query = f"{query} | Target address: {request.target_address}"

    query = f"[{request.audit_type.upper()} AUDIT] {query}"

    logger.info(
        "Audit requested  ▸ session=%s  type=%s  query=%s",
        session_id,
        request.audit_type,
        query[:120],
    )

    start = time.perf_counter()

    try:
        state = await run_audit(query=query, session_id=session_id)
        duration = round(time.perf_counter() - start, 3)

        return AuditResponse(
            session_id=session_id,
            status="completed",
            final_report=state.get("final_report"),
            weilchain_tx_hashes=state.get("weilchain_tx_hashes", []),
            total_steps=len(state.get("weilchain_tx_hashes", [])),
            duration_seconds=duration,
            error=state.get("error"),
        )

    except Exception as exc:
        duration = round(time.perf_counter() - start, 3)
        logger.exception("Audit failed  ▸ session=%s", session_id)
        raise HTTPException(
            status_code=500,
            detail={
                "session_id": session_id,
                "error": f"{type(exc).__name__}: {exc}",
                "duration_seconds": duration,
            },
        ) from exc


# ── GET /audit/{session_id}/trail ────────────────────────────────────────


@router.get("/audit/{session_id}/trail", response_model=AuditTrailResponse)
async def get_audit_trail(session_id: str) -> AuditTrailResponse:
    """Fetch the full on-chain audit trail for a completed session.

    Retrieves every audit-log entry recorded on WeilChain for the
    given ``session_id``.
    """
    logger.info("Trail requested  ▸ session=%s", session_id)

    try:
        entries = await audit_client.get_trail(session_id)
    except Exception as exc:
        logger.exception("Trail fetch failed  ▸ session=%s", session_id)
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch audit trail from WeilChain: {exc}",
        ) from exc

    return AuditTrailResponse(
        session_id=session_id,
        entries=entries,
        total_entries=len(entries),
    )


# ── GET /audit/{session_id}/report ───────────────────────────────────────


@router.get("/audit/{session_id}/report")
async def get_audit_report(session_id: str) -> dict:
    """Retrieve only the final due-diligence report for a session.

    Scans the on-chain audit trail for the entry whose
    ``step_type`` is ``"final_report"`` and returns its payload.
    Returns **404** if no final report exists yet.
    """
    logger.info("Report requested  ▸ session=%s", session_id)

    try:
        entries = await audit_client.get_trail(session_id)
    except Exception as exc:
        logger.exception("Report fetch failed  ▸ session=%s", session_id)
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch audit trail from WeilChain: {exc}",
        ) from exc

    # Find the final_report entry
    for entry in reversed(entries):
        if entry.get("step_type") == "final_report":
            return {
                "session_id": session_id,
                "report": entry.get("payload", entry),
            }

    raise HTTPException(
        status_code=404,
        detail=f"No final report found for session '{session_id}'. "
        f"The audit may still be in progress.",
    )


# ── GET /health ──────────────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check API availability and WeilChain RPC connectivity."""
    connected = await audit_client.health_check()

    return HealthResponse(
        status="ok",
        version="1.0.0",
        weilchain_connected=connected,
    )