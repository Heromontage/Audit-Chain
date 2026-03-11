"""
AuditChain — Web3 MCP Tools Server (WeilChain Applet)

A FastMCP server exposing 8 on-chain data tools that the LangGraph
due-diligence agent can call via langchain-mcp-adapters.

Local dev:   runs as a stdio process (FastMCP)
Production:  deployed as a native WeilChain Applet via
             ``weil applet deploy mcp_applets/ --network testnet``

Tools:
    1. get_wallet_transactions  — Etherscan tx history
    2. get_eth_balance          — Etherscan ETH balance
    3. get_token_transfers      — Etherscan ERC-20 transfers
    4. is_contract_verified     — Etherscan source-code verification
    5. get_token_balances       — Alchemy token balances
    6. get_asset_transfers      — Alchemy asset transfer history
    7. get_token_security       — GoPlus token risk analysis
    8. get_wallet_risk_profile  — GoPlus wallet address risk flags
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx
from mcp.server.fastmcp import FastMCP

# ── FastMCP Server Instance ──────────────────────────────────────────────────

mcp = FastMCP(
    "AuditChain Web3 Tools",
    description=(
        "On-chain data retrieval and security analysis tools for "
        "automated Web3 due diligence.  Deployed as a WeilChain Applet."
    ),
)

# ── Shared Constants ─────────────────────────────────────────────────────────

ETHERSCAN_BASE_URL = "https://api.etherscan.io/api"
GOPLUS_BASE_URL = "https://api.gopluslabs.io/api/v1"
HTTP_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _etherscan_key() -> str:
    """Return the Etherscan API key from the environment."""
    key = os.environ.get("ETHERSCAN_API_KEY", "")
    if not key:
        raise RuntimeError("ETHERSCAN_API_KEY is not set in the environment.")
    return key


def _alchemy_url() -> str:
    """Build the Alchemy JSON-RPC URL from the environment."""
    key = os.environ.get("ALCHEMY_API_KEY", "")
    if not key:
        raise RuntimeError("ALCHEMY_API_KEY is not set in the environment.")
    return f"https://eth-mainnet.g.alchemy.com/v2/{key}"


def _wei_to_eth(wei: str | int) -> float:
    """Convert a Wei string/int to an ETH float."""
    return int(wei) / 1e18


def _unix_to_iso(ts: str | int) -> str:
    """Convert a Unix timestamp to an ISO-8601 string."""
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()


# ═════════════════════════════════════════════════════════════════════════════
#  ETHERSCAN TOOLS (1-4)
# ═════════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_wallet_transactions(address: str, limit: int = 20) -> dict:
    """Fetch the most recent Ethereum transactions for a wallet address.

    Uses the Etherscan ``account/txlist`` endpoint to retrieve normal
    (external) transactions.  Returns a structured summary including
    each transaction's hash, sender, recipient, value in ETH, timestamp,
    and error status.

    Args:
        address: The Ethereum wallet address (0x-prefixed).
        limit:   Maximum number of transactions to return (default 20).

    Returns:
        A dict with keys ``address``, ``transaction_count``, and
        ``transactions`` (list of transaction summaries).
    """
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.get(
            ETHERSCAN_BASE_URL,
            params={
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": limit,
                "sort": "desc",
                "apikey": _etherscan_key(),
            },
        )
        response.raise_for_status()
        data = response.json()

    raw_txs: list[dict] = data.get("result", []) if isinstance(data.get("result"), list) else []

    transactions = [
        {
            "hash": tx.get("hash", ""),
            "from": tx.get("from", ""),
            "to": tx.get("to", ""),
            "value_eth": _wei_to_eth(tx.get("value", "0")),
            "timestamp": _unix_to_iso(tx.get("timeStamp", "0")),
            "is_error": tx.get("isError", "0") == "1",
        }
        for tx in raw_txs
    ]

    return {
        "address": address,
        "transaction_count": len(transactions),
        "transactions": transactions,
    }


@mcp.tool()
async def get_eth_balance(address: str) -> dict:
    """Get the current ETH balance for a wallet address.

    Queries the Etherscan ``account/balance`` endpoint and returns the
    balance in both Wei and ETH.

    Args:
        address: The Ethereum wallet address (0x-prefixed).

    Returns:
        A dict with keys ``address``, ``balance_eth``, and ``balance_wei``.
    """
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.get(
            ETHERSCAN_BASE_URL,
            params={
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest",
                "apikey": _etherscan_key(),
            },
        )
        response.raise_for_status()
        data = response.json()

    balance_wei: str = data.get("result", "0")

    return {
        "address": address,
        "balance_eth": _wei_to_eth(balance_wei),
        "balance_wei": balance_wei,
    }


@mcp.tool()
async def get_token_transfers(address: str, limit: int = 20) -> dict:
    """Fetch recent ERC-20 token transfers for a wallet address.

    Uses the Etherscan ``account/tokentx`` endpoint to list token
    transfer events involving the given address.

    Args:
        address: The Ethereum wallet address (0x-prefixed).
        limit:   Maximum number of transfers to return (default 20).

    Returns:
        A dict with keys ``address``, ``transfer_count``, and
        ``transfers`` (list of transfer summaries including token name,
        symbol, sender, recipient, value, and timestamp).
    """
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.get(
            ETHERSCAN_BASE_URL,
            params={
                "module": "account",
                "action": "tokentx",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": limit,
                "sort": "desc",
                "apikey": _etherscan_key(),
            },
        )
        response.raise_for_status()
        data = response.json()

    raw_transfers: list[dict] = data.get("result", []) if isinstance(data.get("result"), list) else []

    transfers = [
        {
            "token_name": tx.get("tokenName", ""),
            "token_symbol": tx.get("tokenSymbol", ""),
            "from": tx.get("from", ""),
            "to": tx.get("to", ""),
            "value": tx.get("value", "0"),
            "timestamp": _unix_to_iso(tx.get("timeStamp", "0")),
        }
        for tx in raw_transfers
    ]

    return {
        "address": address,
        "transfer_count": len(transfers),
        "transfers": transfers,
    }


@mcp.tool()
async def is_contract_verified(address: str) -> dict:
    """Check whether a smart contract's source code is verified on Etherscan.

    Queries the Etherscan ``contract/getsourcecode`` endpoint and inspects
    the response to determine verification status, contract name, compiler
    version, and whether the contract is a proxy.

    Args:
        address: The smart contract address (0x-prefixed).

    Returns:
        A dict with keys ``address``, ``is_verified``, ``contract_name``,
        ``compiler_version``, and ``is_proxy``.
    """
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.get(
            ETHERSCAN_BASE_URL,
            params={
                "module": "contract",
                "action": "getsourcecode",
                "address": address,
                "apikey": _etherscan_key(),
            },
        )
        response.raise_for_status()
        data = response.json()

    result: list[dict] = data.get("result", [{}])
    contract = result[0] if result else {}

    source_code: str = contract.get("SourceCode", "")
    is_verified = bool(source_code and source_code.strip())

    return {
        "address": address,
        "is_verified": is_verified,
        "contract_name": contract.get("ContractName", ""),
        "compiler_version": contract.get("CompilerVersion", ""),
        "is_proxy": contract.get("Proxy", "0") == "1",
    }


# ═════════════════════════════════════════════════════════════════════════════
#  ALCHEMY TOOLS (5-6)
# ═════════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_token_balances(address: str) -> dict:
    """Get all ERC-20 token balances held by a wallet address.

    Calls the Alchemy ``alchemy_getTokenBalances`` JSON-RPC method to
    retrieve every token the wallet currently holds.

    Args:
        address: The Ethereum wallet address (0x-prefixed).

    Returns:
        A dict with keys ``address``, ``token_count``, and ``tokens``
        (list of token balance objects).
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "alchemy_getTokenBalances",
        "params": [address, "erc20"],
        "id": 1,
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(_alchemy_url(), json=payload)
        response.raise_for_status()
        data = response.json()

    result = data.get("result", {})
    token_balances: list[dict] = result.get("tokenBalances", [])

    tokens = [
        {
            "contract_address": tb.get("contractAddress", ""),
            "balance_raw": tb.get("tokenBalance", "0x0"),
        }
        for tb in token_balances
        if tb.get("tokenBalance") and tb["tokenBalance"] != "0x0"
    ]

    return {
        "address": address,
        "token_count": len(tokens),
        "tokens": tokens,
    }


@mcp.tool()
async def get_asset_transfers(address: str) -> dict:
    """Fetch asset transfer history for a wallet via Alchemy.

    Calls ``alchemy_getAssetTransfers`` with categories ``external``,
    ``erc20``, and ``erc721`` to capture ETH, fungible-token, and
    NFT movements.

    Args:
        address: The Ethereum wallet address (0x-prefixed).

    Returns:
        A dict with keys ``address``, ``transfer_count``, and
        ``transfers`` (list of transfer objects).
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "alchemy_getAssetTransfers",
        "params": [
            {
                "fromAddress": address,
                "category": ["external", "erc20", "erc721"],
                "order": "desc",
                "maxCount": "0x14",  # 20 in hex
                "withMetadata": True,
            }
        ],
        "id": 1,
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(_alchemy_url(), json=payload)
        response.raise_for_status()
        data = response.json()

    result = data.get("result", {})
    raw_transfers: list[dict] = result.get("transfers", [])

    transfers = [
        {
            "from": t.get("from", ""),
            "to": t.get("to", ""),
            "value": t.get("value"),
            "asset": t.get("asset", ""),
            "category": t.get("category", ""),
            "block_num": t.get("blockNum", ""),
            "tx_hash": t.get("hash", ""),
            "metadata": t.get("metadata", {}),
        }
        for t in raw_transfers
    ]

    return {
        "address": address,
        "transfer_count": len(transfers),
        "transfers": transfers,
    }


# ═════════════════════════════════════════════════════════════════════════════
#  GOPLUS SECURITY TOOLS (7-8)
# ═════════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_token_security(contract_address: str, chain_id: int = 1) -> dict:
    """Analyse a token contract for security risks using GoPlus Security API.

    Checks for honeypot behaviour, buy/sell taxes, mintability, proxy
    patterns, and owner concentration — critical signals for Web3
    due diligence.

    Args:
        contract_address: The ERC-20 token contract address (0x-prefixed).
        chain_id:         The chain ID to query (default ``1`` for Ethereum
                          mainnet).

    Returns:
        A dict with keys ``contract``, ``token_name``, ``is_honeypot``,
        ``buy_tax``, ``sell_tax``, ``is_mintable``, ``is_proxy``, and
        ``owner_address``.
    """
    url = f"{GOPLUS_BASE_URL}/token_security/{chain_id}"

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.get(
            url,
            params={"contract_addresses": contract_address.lower()},
        )
        response.raise_for_status()
        data = response.json()

    result: dict = data.get("result", {})
    token_data: dict = result.get(contract_address.lower(), {})

    return {
        "contract": contract_address,
        "token_name": token_data.get("token_name", ""),
        "is_honeypot": token_data.get("is_honeypot", "0") == "1",
        "buy_tax": token_data.get("buy_tax", "0"),
        "sell_tax": token_data.get("sell_tax", "0"),
        "is_mintable": token_data.get("is_mintable", "0") == "1",
        "is_proxy": token_data.get("is_proxy", "0") == "1",
        "owner_address": token_data.get("owner_address", ""),
    }


@mcp.tool()
async def get_wallet_risk_profile(address: str) -> dict:
    """Assess wallet-level risk flags using the GoPlus Security API.

    Checks whether an address has been flagged for phishing, darkweb
    activity, contract abuse, financial crime, or other on-chain risk
    indicators.

    Args:
        address: The Ethereum wallet address (0x-prefixed).

    Returns:
        A dict with keys ``address``, ``risk_flags`` (list of human-
        readable risk labels), and ``is_risky`` (boolean).
    """
    url = f"{GOPLUS_BASE_URL}/address_security"

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.get(
            url,
            params={"address": address.lower()},
        )
        response.raise_for_status()
        data = response.json()

    result: dict = data.get("result", {})

    # GoPlus returns "1" for flagged risk categories
    risk_label_map: dict[str, str] = {
        "honeypot_related_address": "Honeypot-related address",
        "phishing_activities": "Phishing activity detected",
        "blackmail_activities": "Blackmail activity detected",
        "stealing_attack": "Stealing/drainer attack",
        "fake_kyc": "Fake KYC detected",
        "malicious_mining_activities": "Malicious mining activity",
        "darkweb_transactions": "Darkweb transactions",
        "cybercrime": "Cybercrime association",
        "money_laundering": "Money laundering",
        "financial_crime": "Financial crime",
        "blacklist_doubt": "Blacklist suspicion",
        "data_source": "Flagged by external data source",
    }

    risk_flags: list[str] = [
        label
        for key, label in risk_label_map.items()
        if result.get(key, "0") == "1"
    ]

    return {
        "address": address,
        "risk_flags": risk_flags,
        "is_risky": len(risk_flags) > 0,
    }


# ── DEPLOY TO WEILCHAIN ──────────────────────────────────────
# 1. npm install -g @weilliptic/cli
# 2. weil auth login
# 3. weil applet deploy mcp_applets/ --network testnet
# 4. Copy the applet address → WEILCHAIN_APPLET_ID in .env
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")