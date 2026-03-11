"""
AuditChain — FastAPI Application Entrypoint

Launches the AuditChain API server with:
  • CORS middleware (permissive for development)
  • Lifespan hooks for startup logging and graceful shutdown
  • All routes mounted at ``/api/v1``

Run locally:
    python main.py            # uvicorn with hot-reload on :8000
    uvicorn main:app --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config import settings
from weilchain.audit_client import audit_client

# ── Logging ───────────────────────────────────────────────────────────────

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — startup and shutdown hooks."""

    # ── Startup ───────────────────────────────────────────────────────────
    logger.info(
        "AuditChain starting on WeilChain [%s]  ▸ rpc=%s  env=%s",
        settings.WEILCHAIN_NETWORK,
        settings.WEILCHAIN_RPC_URL,
        settings.APP_ENV,
    )

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────
    logger.info("AuditChain shutting down — closing WeilChain client…")
    await audit_client.close()
    logger.info("Goodbye.")


# ── FastAPI App ───────────────────────────────────────────────────────────

app = FastAPI(
    title="AuditChain API",
    description=(
        "LangGraph AI agent for automated Web3 due diligence "
        "with immutable on-chain audit trails via WeilChain (Weilliptic)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount Routes ──────────────────────────────────────────────────────────

app.include_router(router)


# ── Development Server ───────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)