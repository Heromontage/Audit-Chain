"""
AuditChain — Pydantic v2 Request / Response Schemas

All API models used by the FastAPI routes.  Strict validation ensures
malformed requests are rejected before reaching the agent.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ── Request Models ────────────────────────────────────────────────────────


class AuditRequest(BaseModel):
    """Payload for launching a new Web3 due-diligence audit session.

    Attributes
    ----------
    query:
        Natural-language audit instruction (minimum 10 characters).
    target_address:
        Optional Ethereum address to focus the audit on.  If provided
        it is appended to the query before the agent begins.
    audit_type:
        Category hint that helps the planner choose the right tools.
    """

    query: str = Field(
        ...,
        min_length=10,
        description="Natural-language Web3 audit query (min 10 chars).",
        examples=["Audit wallet 0xABC… for rug-pull risk indicators"],
    )
    target_address: str | None = Field(
        default=None,
        description="Optional 0x-prefixed Ethereum address to focus on.",
        examples=["0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"],
    )
    audit_type: Literal["wallet", "contract", "token", "general"] = Field(
        default="general",
        description="Category of the audit — helps the planner pick tools.",
    )


# ── Response Models ───────────────────────────────────────────────────────


class AuditResponse(BaseModel):
    """Response returned after an audit session completes.

    Attributes
    ----------
    session_id:
        Unique identifier for the completed session.
    status:
        Human-readable status (``"completed"`` or ``"error"``).
    final_report:
        Structured due-diligence report, or ``None`` on failure.
    weilchain_tx_hashes:
        List of on-chain transaction hashes — immutable proof of
        every agent step.
    total_steps:
        Number of steps the agent executed (including planning &
        final report).
    duration_seconds:
        Wall-clock time the audit took, in seconds.
    error:
        Error message if the audit failed, otherwise ``None``.
    """

    session_id: str
    status: str
    final_report: dict | None = None
    weilchain_tx_hashes: list[str] = Field(default_factory=list)
    total_steps: int = 0
    duration_seconds: float = 0.0
    error: str | None = None


class AuditTrailResponse(BaseModel):
    """Response containing the full on-chain audit trail for a session.

    Attributes
    ----------
    session_id:
        The session whose trail was fetched.
    entries:
        Ordered list of audit-log entries from WeilChain.
    total_entries:
        Number of entries returned.
    """

    session_id: str
    entries: list[dict] = Field(default_factory=list)
    total_entries: int = 0


class HealthResponse(BaseModel):
    """Response from the health-check endpoint.

    Attributes
    ----------
    status:
        ``"ok"`` if the API is running.
    version:
        Semantic version string of the AuditChain API.
    weilchain_connected:
        ``True`` if the WeilChain RPC endpoint is reachable.
    """

    status: str
    version: str
    weilchain_connected: bool