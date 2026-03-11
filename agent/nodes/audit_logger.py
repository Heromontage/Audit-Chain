"""
AuditChain — Audit Logger Node

Runs **after every tool execution / reasoning step** to push an
immutable audit-log entry to WeilChain.  The returned ``tx_hash``
is appended to ``state["weilchain_tx_hashes"]`` — building up an
on-chain proof chain for the entire session.

After logging, the node increments ``current_step_index`` so the
graph advances to the next planned step.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from agent.state import AgentState
from weilchain.audit_client import audit_client

logger = logging.getLogger(__name__)

# Maximum characters for summary strings sent on-chain
_MAX_SUMMARY_LEN = 500


def _summarise(obj: Any, max_len: int = _MAX_SUMMARY_LEN) -> str:
    """Create a truncated string summary of an arbitrary object."""
    try:
        text = json.dumps(obj, default=str)
    except (TypeError, ValueError):
        text = str(obj)
    return text[:max_len] + ("…" if len(text) > max_len else "")


async def audit_logger_node(state: AgentState) -> AgentState:
    """Log the current step to WeilChain and advance the step index.

    Parameters
    ----------
    state:
        Current agent state.  Expects ``tool_results`` to contain at
        least one entry for the current step.

    Returns
    -------
    AgentState
        Updated state with a new audit log entry, a new WeilChain
        ``tx_hash``, and ``current_step_index`` incremented by 1.
    """
    session_id: str = state["session_id"]
    step_index: int = state["current_step_index"]
    planned_steps: list[dict] = state["planned_steps"]
    tool_results: list[dict] = state["tool_results"]
    tx_hashes: list[str] = state["weilchain_tx_hashes"]

    # ── Gather context for the log entry ──────────────────────────────────

    current_step: dict = (
        planned_steps[step_index] if step_index < len(planned_steps) else {}
    )
    step_type: str = current_step.get("step_type", "unknown")
    tool_name: str | None = current_step.get("tool_name")

    # Find the matching tool result for this step
    latest_result: dict = {}
    for tr in reversed(tool_results):
        if tr.get("step_index") == step_index:
            latest_result = tr
            break

    input_summary = _summarise(current_step.get("tool_args", {}))
    output_summary = _summarise(
        latest_result.get("result") or latest_result.get("error") or ""
    )

    # ── Build the on-chain audit entry ────────────────────────────────────

    entry: dict[str, Any] = {
        "session_id": session_id,
        "step_index": step_index,
        "step_type": step_type,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_summary": input_summary,
        "output_summary": output_summary,
        "tool_name": tool_name,
        "llm_model": "gpt-4o",
        "token_usage": {},
        "tx_hash_prev": tx_hashes[-1] if tx_hashes else None,
    }

    # ── Push to WeilChain ─────────────────────────────────────────────────

    tx_hash = await audit_client.log(
        session_id=session_id,
        step_index=step_index,
        step_type=step_type,
        payload=entry,
    )

    entry["tx_hash"] = tx_hash

    logger.info(
        "Audit logged  ▸ session=%s  step=%d  type=%s  tx=%s",
        session_id,
        step_index,
        step_type,
        tx_hash,
    )

    # ── Update state ──────────────────────────────────────────────────────

    state["audit_logs"].append(entry)
    state["weilchain_tx_hashes"].append(tx_hash)
    state["current_step_index"] = step_index + 1

    return state