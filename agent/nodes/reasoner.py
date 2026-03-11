"""
AuditChain — Reasoner Node

Decides whether the agent loop should **CONTINUE** to the next step
or declare itself **DONE**.  The decision is made by GPT-4o after
reviewing all tool results collected so far against the original query.

The reasoner sets ``state["is_complete"]`` which the LangGraph
conditional edge uses to route to either the next iteration or the
reporter node.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_openai import ChatOpenAI

from agent.state import AgentState

logger = logging.getLogger(__name__)

# ── System prompt for the reasoning LLM ──────────────────────────────────

REASONER_SYSTEM_PROMPT = """\
You are AuditChain Reasoner — an expert at evaluating whether enough
on-chain evidence has been gathered for a Web3 due-diligence report.

You will be given:
  1. The original audit query.
  2. The planned investigation steps.
  3. All tool results collected so far.

Respond with ONLY a JSON object:
{
  "decision": "CONTINUE" | "DONE",
  "reasoning": "<1-3 sentence explanation>"
}

Rules:
- "DONE"     → all planned steps are complete OR you have sufficient data.
- "CONTINUE" → remaining steps still exist AND more data is needed.
- Return ONLY the JSON object — no markdown fences, no explanation.
"""


async def reasoner_node(state: AgentState) -> AgentState:
    """Evaluate collected evidence and decide CONTINUE vs DONE.

    Parameters
    ----------
    state:
        Current agent state with ``tool_results``, ``planned_steps``,
        and ``current_step_index``.

    Returns
    -------
    AgentState
        Updated state with ``is_complete`` set and ``reasoning``
        appended to ``llm_reasoning_history``.
    """
    query: str = state["query"]
    planned_steps: list[dict] = state["planned_steps"]
    tool_results: list[dict] = state["tool_results"]
    current_index: int = state["current_step_index"]

    # ── Quick check: all steps already done ───────────────────────────────

    all_steps_done = current_index >= len(planned_steps)

    # ── Ask GPT-4o to reason ──────────────────────────────────────────────

    user_message = json.dumps(
        {
            "query": query,
            "planned_steps": planned_steps,
            "current_step_index": current_index,
            "total_steps": len(planned_steps),
            "all_steps_completed": all_steps_done,
            "tool_results_so_far": [
                {
                    "step_index": tr.get("step_index"),
                    "tool_name": tr.get("tool_name"),
                    "has_result": tr.get("result") is not None,
                    "has_error": tr.get("error") is not None,
                }
                for tr in tool_results
            ],
        },
        default=str,
    )

    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

    response = await llm.ainvoke(
        [
            {"role": "system", "content": REASONER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
    )

    # ── Parse the decision ────────────────────────────────────────────────

    raw_content: str = response.content  # type: ignore[union-attr]

    try:
        decision_obj: dict[str, Any] = json.loads(raw_content)
        decision: str = decision_obj.get("decision", "DONE").upper()
        reasoning: str = decision_obj.get("reasoning", "No reasoning provided.")
    except (json.JSONDecodeError, ValueError):
        logger.warning("Reasoner returned unparseable JSON — defaulting to DONE.")
        decision = "DONE"
        reasoning = f"Defaulted to DONE (unparseable response): {raw_content[:200]}"

    # Force DONE if we've exhausted all planned steps
    if all_steps_done:
        decision = "DONE"
        reasoning = (
            f"All {len(planned_steps)} planned steps completed. "
            f"Original reasoning: {reasoning}"
        )

    is_complete = decision == "DONE"

    logger.info(
        "Reasoner decision  ▸ %s  (step %d/%d)  reason: %s",
        decision,
        current_index,
        len(planned_steps),
        reasoning,
    )

    # ── Update state ──────────────────────────────────────────────────────

    state["is_complete"] = is_complete
    state["llm_reasoning_history"].append(reasoning)

    return state