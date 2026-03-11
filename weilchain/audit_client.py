"""
WeilChain Audit Client — immutable on-chain audit-trail logging.

Every AI-agent step is POSTed to the WeilChain RPC (by Weilliptic) and
anchored as a verifiable on-chain record.  The returned ``tx_hash`` serves
as cryptographic proof that the step was logged.

Usage:
    from weilchain.audit_client import audit_client

    tx = await audit_client.log(
        session_id="sess_abc123",
        step_index=0,
        step_type="contract_fetch",
        payload={"address": "0x..."},
    )
"""

# TODO: Replace HTTP call with:
#   tx = await AuditClient(api_key).log(...)
# once weilchain-audit-sdk is installed
# (pip install weilchain-audit-sdk  —  docs: https://docs.weilliptic.ai)

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)


# ── Custom Exception ─────────────────────────────────────────────────────────


class WeilChainError(Exception):
    """Raised when a WeilChain RPC interaction fails."""


# ── Audit Client ─────────────────────────────────────────────────────────────


class WeilChainAuditClient:
    """Async client for logging AI-agent steps to the WeilChain audit trail.

    Parameters
    ----------
    api_key:
        WeilChain API key issued at https://weilliptic.ai/get-started.
    network:
        Target network — ``"testnet"`` or ``"mainnet"``.
    rpc_url:
        WeilChain JSON-RPC endpoint
        (e.g. ``https://rpc.testnet.weilliptic.ai``).
    """

    _client: httpx.AsyncClient | None

    def __init__(
        self,
        api_key: str,
        network: str,
        rpc_url: str,
    ) -> None:
        self._api_key = api_key
        self._network = network
        self._rpc_url = rpc_url.rstrip("/")
        self._client = None  # lazily created on first call

    # ── Helpers ───────────────────────────────────────────────────────────

    def _ensure_client(self) -> httpx.AsyncClient:
        """Return the shared ``httpx.AsyncClient``, creating it if needed."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._rpc_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "X-WeilChain-Network": self._network,
                },
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    @staticmethod
    def _local_fallback() -> str:
        """Generate a deterministic local-fallback identifier."""
        return f"LOCAL_FALLBACK:{datetime.now(timezone.utc).isoformat()}"

    # ── Public API ────────────────────────────────────────────────────────

    async def log(
        self,
        session_id: str,
        step_index: int,
        step_type: str,
        payload: dict[str, Any],
    ) -> str:
        """Log a single agent step to the WeilChain audit trail.

        Parameters
        ----------
        session_id:
            Unique identifier for the current audit session.
        step_index:
            Zero-based ordinal of this step within the session.
        step_type:
            Human-readable label (e.g. ``"contract_fetch"``,
            ``"risk_score"``, ``"llm_call"``).
        payload:
            Arbitrary JSON-serialisable data captured at this step.

        Returns
        -------
        str
            The on-chain ``tx_hash`` confirming the record, **or** a
            ``LOCAL_FALLBACK:<iso-timestamp>`` string if the RPC call
            failed for any reason.  This method **never raises**.
        """
        # TODO: Replace HTTP call with:
        #   tx = await AuditClient(api_key).log(...)
        # once weilchain-audit-sdk is installed

        try:
            client = self._ensure_client()

            body: dict[str, Any] = {
                "jsonrpc": "2.0",
                "method": "audit_log",
                "params": {
                    "session_id": session_id,
                    "step_index": step_index,
                    "step_type": step_type,
                    "payload": payload,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "id": step_index,
            }

            response = await client.post("/v1/audit", json=body)
            response.raise_for_status()

            data = response.json()

            # Extract tx_hash — handle both JSON-RPC result and REST shapes
            tx_hash: str = (
                data.get("result", {}).get("tx_hash")
                or data.get("tx_hash")
                or ""
            )

            if not tx_hash:
                raise WeilChainError(
                    f"WeilChain RPC returned no tx_hash: {data}"
                )

            logger.info(
                "Audit step logged  ▸ session=%s  step=%d  type=%s  tx=%s",
                session_id,
                step_index,
                step_type,
                tx_hash,
            )
            return tx_hash

        except Exception as exc:
            fallback = self._local_fallback()
            logger.warning(
                "WeilChain audit log failed (using local fallback)  "
                "▸ session=%s  step=%d  error=%s  fallback=%s",
                session_id,
                step_index,
                exc,
                fallback,
            )
            return fallback

    async def get_trail(self, session_id: str) -> list[dict[str, Any]]:
        """Retrieve the full audit trail for a given session.

        Parameters
        ----------
        session_id:
            The session whose audit entries should be fetched.

        Returns
        -------
        list[dict[str, Any]]
            Ordered list of audit-log entries.  Returns an empty list
            if the RPC call fails.

        Raises
        ------
        WeilChainError
            If the RPC returns a non-2xx status or an unparseable body.
        """
        try:
            client = self._ensure_client()

            response = await client.get(
                "/v1/audit/trail",
                params={"session_id": session_id},
            )
            response.raise_for_status()

            data = response.json()

            # Support both JSON-RPC envelope and flat list responses
            entries: list[dict[str, Any]] = (
                data.get("result", {}).get("entries")
                or data.get("entries")
                or data if isinstance(data, list) else []
            )

            logger.info(
                "Audit trail fetched  ▸ session=%s  entries=%d",
                session_id,
                len(entries),
            )
            return entries

        except Exception as exc:
            raise WeilChainError(
                f"Failed to fetch audit trail for session {session_id!r}: {exc}"
            ) from exc

    async def health_check(self) -> bool:
        """Return ``True`` if the WeilChain RPC endpoint is reachable.

        Performs a lightweight GET against the RPC root and considers
        any 2xx response a success.
        """
        try:
            client = self._ensure_client()
            response = await client.get("/health")
            return response.is_success
        except Exception as exc:
            logger.warning("WeilChain health-check failed: %s", exc)
            return False

    async def close(self) -> None:
        """Gracefully close the underlying ``httpx.AsyncClient``."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            logger.debug("WeilChain HTTP client closed.")


# ── Module-level singleton ────────────────────────────────────────────────────
# Initialised once on first import; every other module simply does:
#     from weilchain.audit_client import audit_client

audit_client: WeilChainAuditClient = WeilChainAuditClient(
    api_key=settings.WEILCHAIN_API_KEY.get_secret_value(),
    network=settings.WEILCHAIN_NETWORK,
    rpc_url=settings.WEILCHAIN_RPC_URL,
)