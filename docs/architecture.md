# AuditChain — Technical Architecture

## System Overview

AuditChain is a **LangGraph-powered AI agent** that performs automated Web3 due diligence and logs every decision step onto **WeilChain** (by Weilliptic) as an immutable on-chain audit trail.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND                                   │
│                     React + Vite + Tailwind                         │
│                                                                     │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │ LandingPage  │    │   AuditPage      │    │   api.js         │  │
│  │ Marketing    │    │   Audit Form     │    │   fetch wrapper  │  │
│  │ /            │    │   Report Viewer  │    │   → /api/v1/*    │  │
│  └──────────────┘    │   Proof Links    │    └──────────────────┘  │
│                      └──────────────────┘                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP (proxied via Vite → :8000)
┌──────────────────────��───────▼──────────────────────────────────────┐
│                        BACKEND (FastAPI)                             │
│                         main.py :8000                               │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ api/routes.py                                                  │ │
│  │   POST /api/v1/audit         → run_audit()                    │ │
│  │   GET  /api/v1/audit/:id/trail → audit_client.get_trail()     │ │
│  │   GET  /api/v1/audit/:id/report → find final_report entry     │ │
│  │   GET  /api/v1/health        → audit_client.health_check()    │ │
│  └──────────────────────┬─────────────────────────────────────────┘ │
│                          │                                           │
│  ┌───────────────────────▼─────────────────────────────────────────┐│
│  │ agent/graph.py — LangGraph StateGraph                           ││
│  │                                                                  ││
│  │   START                                                          ││
│  │     │                                                            ││
│  │     ▼                                                            ││
│  │   ┌──────────┐                                                   ││
│  │   │ PLANNER  │ GPT-4o decomposes query → 3-6 steps              ││
│  │   └────┬─────┘                                                   ││
│  │        ▼                                                         ││
│  │   ┌──────────────┐    stdio     ┌───────────────────────┐       ││
│  │   │TOOL_EXECUTOR │◄────────────►│ mcp_applets/          │       ││
│  │   │              │   MCP        │ web3_tools_servers.py  │       ││
│  │   └────┬─────────┘              │ (8 Web3 tools)        │       ││
│  │        ▼                        └───��───────────────────┘       ││
│  │   ┌──────────────┐    httpx     ┌───────────────────────┐       ││
│  │   │AUDIT_LOGGER  │────────────►│ WeilChain RPC          │       ││
│  │   │              │  POST /v1/  │ rpc.testnet.weilliptic │       ││
│  │   └────┬─────────┘  audit      │ .ai                   │       ││
│  │        ▼                        └───────────────────────┘       ││
│  │   ┌──────────┐                                                   ││
│  │   │ REASONER │ CONTINUE → loop back to TOOL_EXECUTOR             ││
│  │   │          │ DONE     → proceed to REPORTER                    ││
│  │   └────┬─────┘                                                   ││
│  │        ▼                                                         ││
│  │   ┌──────────┐                                                   ││
│  │   │ REPORTER │ GPT-4o synthesises final report                   ││
│  │   │          │ Logs to WeilChain → tx_hash as final proof        ││
│  │   └────┬─────┘                                                   ││
│  │        ▼                                                         ││
│  │      END                                                         ││
│  └──────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘

External APIs:
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │  Etherscan   │  │   Alchemy    │  │    GoPlus    │
  │  API         │  │   JSON-RPC   │  │  Security    │
  │  (4 tools)   │  │  (2 tools)   │  │  (2 tools)   │
  └──────────────┘  └──────────────┘  └──────────────┘
```

## Data Flow

1. **User** submits audit query via frontend (`POST /api/v1/audit`)
2. **FastAPI** generates `session_id`, calls `run_audit()`
3. **Planner** (GPT-4o) decomposes query into 3–6 steps
4. **Tool Executor** invokes MCP tools (Etherscan, Alchemy, GoPlus) via stdio
5. **Audit Logger** pushes structured log to WeilChain RPC → receives `tx_hash`
6. **Reasoner** (GPT-4o) decides: CONTINUE loop or DONE
7. **Reporter** (GPT-4o) synthesises all evidence into structured report
8. **Response** returned with report + all `tx_hash` values as on-chain proof

## On-Chain Audit Schema

Each WeilChain log entry contains:

```json
{
  "session_id": "uuid",
  "step_index": 0,
  "step_type": "tool_call | llm_reasoning | planning | final_report",
  "timestamp_utc": "ISO-8601",
  "input_summary": "truncated input",
  "output_summary": "truncated output",
  "tool_name": "get_wallet_transactions | null",
  "llm_model": "gpt-4o",
  "token_usage": {},
  "tx_hash_prev": "previous tx_hash (chain linking)"
}
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React + Vite + Tailwind | Interactive audit dashboard |
| API | FastAPI + Pydantic v2 | REST endpoints + validation |
| Agent | LangGraph (StateGraph) | Multi-step agent orchestration |
| LLM | OpenAI GPT-4o | Planning, reasoning, reporting |
| Tools | FastMCP (MCP Protocol) | Web3 data retrieval tools |
| Audit | WeilChain RPC (httpx) | Immutable on-chain logging |
| Data | Etherscan, Alchemy, GoPlus | On-chain data sources |