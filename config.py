"""
AuditChain — Centralised configuration via pydantic-settings.

All values are loaded from environment variables (or a .env file in the
project root).  Import the ready-made singleton anywhere:

    from config import settings
"""

from __future__ import annotations

from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated application settings for AuditChain."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── LLM / AI ──────────────────────────────────────────────
    OPENAI_API_KEY: SecretStr

    # ── Blockchain data providers ─────────────────────────────
    ETHERSCAN_API_KEY: SecretStr
    ALCHEMY_API_KEY: SecretStr

    # ── WeilChain (Weilliptic) audit-trail logging ────────────
    WEILCHAIN_API_KEY: SecretStr
    WEILCHAIN_NETWORK: Literal["testnet", "mainnet"] = "testnet"
    WEILCHAIN_RPC_URL: str = "https://rpc.testnet.weilliptic.ai"
    WEILCHAIN_APPLET_ID: str = ""

    # ── Application ───────────────────────────────────────────
    APP_ENV: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: Literal[
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    ] = "INFO"


# ── Module-level singleton ────────────────────────────────────
# Instantiated once on first import; every other module simply does:
#     from config import settings
settings: Settings = Settings()