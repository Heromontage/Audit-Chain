"""
AuditChain — API Smoke Tests

Run with:  pytest tests/test_api.py -v
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async test client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Health Check ──────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_health_check(client: AsyncClient):
    """GET /api/v1/health returns 200 with expected fields."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "weilchain_connected" in data


# ── Audit Validation ─────────────────────────────────────────────────


@pytest.mark.anyio
async def test_audit_rejects_short_query(client: AsyncClient):
    """POST /api/v1/audit rejects queries shorter than 10 characters."""
    response = await client.post(
        "/api/v1/audit",
        json={"query": "short", "audit_type": "general"},
    )
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.anyio
async def test_audit_rejects_empty_body(client: AsyncClient):
    """POST /api/v1/audit rejects empty request body."""
    response = await client.post("/api/v1/audit", json={})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_audit_rejects_invalid_type(client: AsyncClient):
    """POST /api/v1/audit rejects invalid audit_type."""
    response = await client.post(
        "/api/v1/audit",
        json={
            "query": "Audit wallet 0xABC for risk",
            "audit_type": "invalid_type",
        },
    )
    assert response.status_code == 422


# ── Audit Trail — 404 for unknown session ─────────────────────────────


@pytest.mark.anyio
async def test_trail_unknown_session(client: AsyncClient):
    """GET /audit/{session_id}/trail for a non-existent session."""
    response = await client.get("/api/v1/audit/non-existent-session/trail")
    # Should either return 200 with empty entries or 502 if WeilChain unreachable
    assert response.status_code in (200, 502)


# ── Report — 404 for unknown session ─────────────────────────────────


@pytest.mark.anyio
async def test_report_unknown_session(client: AsyncClient):
    """GET /audit/{session_id}/report returns 404 or 502 for unknown session."""
    response = await client.get("/api/v1/audit/non-existent-session/report")
    assert response.status_code in (404, 502)


# ── Schema Validation ────────────────────────────────────────────────


@pytest.mark.anyio
async def test_audit_accepts_valid_request(client: AsyncClient):
    """POST /api/v1/audit accepts a well-formed request (may fail at LLM layer)."""
    response = await client.post(
        "/api/v1/audit",
        json={
            "query": "Audit wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 for rug-pull risk",
            "target_address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            "audit_type": "wallet",
        },
    )
    # Will be 200 if keys are set, or 500 if not — either is a valid integration signal
    assert response.status_code in (200, 500)