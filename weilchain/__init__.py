"""WeilChain integration package for AuditChain."""

from weilchain.audit_client import WeilChainAuditClient, WeilChainError, audit_client

__all__ = [
    "WeilChainAuditClient",
    "WeilChainError",
    "audit_client",
]