"""
AuditChain — Reporter Node

Final node in the LangGraph loop.  Synthesises **all** collected
evidence (tool results, reasoning history, audit logs) into a
structured due-diligence report.

The report is logged to WeilChain as the ``"final_report"`` step,
completing the immutable on-chain audit trail for the session.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_openai import ChatOpenAI

from agent.state import AgentState
from weilchain.audit_client import audit_client

logger = logging.getLogger(__name__)

# ── System prompt for the reporting LLM ──────────────────────────────────

REPORTER_SYSTEM_PROMPT = """\
You are AuditChain Reporter — a Web3 due-diligence report writer.

You will be given all on-chain evidence, tool results, and reasoning
from an automated audit session.

Produce a single JSON object with this EXACT schema:
{
  "summary": "<2-4 sentence executive summary>",
  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "findings": [
    {"category": "<string>", "detail": "<string>", "severity": "LOW"|"MEDIUM"|"HIGH"|"CRITICAL"}
  ],
  "red_flags": ["<string>", ...],
  "recommendation": "<1-3 sentence actionable recommendation>"
}

Rules:
- Base findings ONLY on the provided evidence.
- risk_level reflects the worst-case finding.
- red_flags is a flat list of concise human-readable warnings.
- Return ONLY the JSON object — no markdown fences, no explanation.
"""


async def reporter_node(state: AgentState) -> AgentState:
    """Generate the final structured due-diligence report.

    Sends all accumulated evidence to GPT-4o, parses the structured
    report, enriches it with on-chain proof metadata, logs it to
    WeilChain, and stores it in ``state["final_report"]``.

    Parameters
    ----------
    state:
        Current agent state with ``tool_results``, ``llm_reasoning_history``,
        ``audit_logs``, and ``weilchain_tx_hashes`` fully populated.

    Returns
    -------
    AgentState
        Updated state with ``final_report`` set and ``is_complete = True``.
    """
    session_id: str = state["session_id"]
    query: str = state["query"]
    tool_results: list[dict] = state["tool_results"]
    reasoning_history: list[str] = state["llm_reasoning_history"]
    tx_hashes: list[str] = state["weilchain_tx_hashes"]

    # ── Build the evidence payload for the LLM ────────────────────────────

    evidence = json.dumps(
        {
            "original_query": query,
            "tool_results": [
                {
                    "step_index": tr.get("step_index"),
                    "tool_name": tr.get("tool_name"),
                    "result": tr.get("result"),
                    "error": tr.get("error"),
                }
                for tr in tool_results
            ],
            "llm_reasoning_history": reasoning_history,
        },
        default=str,
    )

    # ── Ask GPT-4o to write the report ────────────────────────────────────

    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

    response = await llm.ainvoke(
        [
            {"role": "system", "content": REPORTER_SYSTEM_PROMPT},
            {"role": "user", "content": evidence},
        ]
    )

    raw_content: str = response.content  # type: ignore[union-attr]

    # ── Parse the report ──────────────────────────────────────────────────

    try:
        report: dict[str, Any] = json.loads(raw_content)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Reporter returned unparseable JSON: %s", exc)
        report = {
            "summary": "Report generation failed — see raw LLM output.",
            "risk_level": "HIGH",
            "findings": [
                {
                    "category": "report_error",
                    "detail": f"Unparseable LLM response: {raw_content[:300]}",
                    "severity": "HIGH",
                }
            ],
            "red_flags": ["Automated report generation failed"],
            "recommendation": "Manual review required.",
        }

    # ── Enrich with on-chain proof ──────────���─────────────────────────────

    report["on_chain_proof"] = {
        "session_id": session_id,
        "weilchain_tx_hashes": tx_hashes,
        "total_steps": len(tx_hashes),
    }

    # ── Log the final report to WeilChain ─────────────────────────────────

    step_index = state["current_step_index"]

    tx_hash = await audit_client.log(
        session_id=session_id,
        step_index=step_index,
        step_type="final_report",
        payload={
            "summary": report.get("summary", ""),
            "risk_level": report.get("risk_level", ""),
            "findings_count": len(report.get("findings", [])),
            "red_flags_count": len(report.get("red_flags", [])),
        },
    )

    report["on_chain_proof"]["final_report_tx_hash"] = tx_hash
    state["weilchain_tx_hashes"].append(tx_hash)
    state["audit_logs"].append(
        {
            "step_index": step_index,
            "step_type": "final_report",
            "summary": report.get("summary", "")[:200],
            "tx_hash": tx_hash,
        }
    )

    logger.info(
        "Final report generated  ▸ session=%s  risk=%s  findings=%d  tx=%s",
        session_id,
        report.get("risk_level"),
        len(report.get("findings", [])),
        tx_hash,
    )

    # ── Update state ──────────────────────────────────────────────────────

    state["final_report"] = report
    state["is_complete"] = True

    return state