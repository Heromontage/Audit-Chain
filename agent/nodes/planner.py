"""
AuditChain — Planner Node

First node in the LangGraph loop.  Takes the raw user query and asks
GPT-4o to decompose it into 3–6 concrete investigation steps.  Each
step specifies a ``tool_call`` or ``llm_reasoning`` action that
downstream nodes will execute.

The plan itself is logged to WeilChain as the ``"planning"`` step so
the entire audit trail begins on-chain from the very first action.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_openai import ChatOpenAI

from agent.state import AgentState
from weilchain.audit_client import audit_client

logger = logging.getLogger(__name__)

# ── System prompt for the planning LLM ────────────────────────────────────

PLANNER_SYSTEM_PROMPT = """\
You are AuditChain Planner — a Web3 due-diligence planning specialist.

Given the user's audit query, decompose it into 3–6 concrete investigation
steps.  Each step MUST be one of:

  • tool_call      — invokes an MCP tool to fetch on-chain data
  • llm_reasoning  — uses the LLM to analyse / synthesise results

Available MCP tools (use these exact names):
  get_wallet_transactions, get_eth_balance, get_token_transfers,
  is_contract_verified, get_token_balances, get_asset_transfers,
  get_token_security, get_wallet_risk_profile

Respond with ONLY a JSON array.  Each element:
{
  "step_type": "tool_call" | "llm_reasoning",
  "description": "<what this step does>",
  "tool_name": "<exact tool name or null if llm_reasoning>",
  "tool_args": {<arg_name: value>}  // empty {} if llm_reasoning
}

Rules:
- Always start with data-gathering tool_call steps before llm_reasoning.
- Include at least one security-related check (token_security or wallet_risk_profile).
- Return ONLY the JSON array — no markdown fences, no explanation.
"""


async def planner_node(state: AgentState) -> AgentState:
    """Decompose the audit query into an ordered list of investigation steps.

    Parameters
    ----------
    state:
        Current agent state containing at minimum ``session_id`` and ``query``.

    Returns
    -------
    AgentState
        Updated state with ``planned_steps`` populated, ``current_step_index``
        set to ``0``, ``is_complete`` set to ``False``, and the planning
        step logged to WeilChain.
    """
    query: str = state["query"]
    session_id: str = state["session_id"]

    # ── Ask GPT-4o to build the plan ──────────────────────────────────────

    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

    response = await llm.ainvoke(
        [
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]
    )

    # ── Parse the plan ────────────────────────────────────────────────────

    raw_content: str = response.content  # type: ignore[union-attr]

    try:
        planned_steps: list[dict[str, Any]] = json.loads(raw_content)
        if not isinstance(planned_steps, list):
            raise ValueError("Expected a JSON array of steps.")
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Planner returned unparseable JSON: %s", exc)
        planned_steps = [
            {
                "step_type": "llm_reasoning",
                "description": f"Analyse the query directly: {query}",
                "tool_name": None,
                "tool_args": {},
            }
        ]

    logger.info(
        "Planner produced %d steps for session %s",
        len(planned_steps),
        session_id,
    )

    # ── Log the planning step to WeilChain ────────────────────────────────

    tx_hash = await audit_client.log(
        session_id=session_id,
        step_index=0,
        step_type="planning",
        payload={
            "query": query,
            "planned_steps": planned_steps,
        },
    )

    # ── Update state ──────────────────────────────────────────────────────

    state["planned_steps"] = planned_steps
    state["current_step_index"] = 0
    state["is_complete"] = False
    state["audit_logs"].append(
        {
            "step_index": 0,
            "step_type": "planning",
            "summary": f"Planned {len(planned_steps)} steps",
            "tx_hash": tx_hash,
        }
    )
    state["weilchain_tx_hashes"].append(tx_hash)

    return state