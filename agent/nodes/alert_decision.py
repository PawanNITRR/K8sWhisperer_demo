from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from schemas.models import AlertDecision
from agent.llm_factory import get_chat_model
from agent.prompts_util import load_prompt
from agent.state import AgentState
from utils.structured_logger import get_logger

log = get_logger(__name__)


def alert_decision_node(state: AgentState) -> dict[str, Any]:
    """
    Intelligently decide whether to send a Slack alert based on anomaly context.
    Uses LLM reasoning with structured output to evaluate severity, confidence,
    blast radius, execution success, and other factors.
    """
    primary_anomaly = state.get("primary_anomaly")
    diagnosis = state.get("diagnosis", "")
    plan = state.get("plan")
    result = state.get("result", "")
    should_auto_execute = state.get("should_auto_execute", False)
    approved = state.get("approved")

    # If no primary anomaly, no alert needed
    if not primary_anomaly:
        log.info("Alert decision: no primary anomaly, should_alert=False")
        return {"should_alert": False, "alert_reason": "No anomaly detected"}

    # Prepare context for LLM decision
    context = {
        "anomaly": primary_anomaly,
        "diagnosis": diagnosis,
        "plan": plan,
        "execution_result": result,
        "auto_executed": should_auto_execute,
        "human_approved": approved,
        "cycle_id": state.get("cycle_id", "unknown")
    }

    # Use LLM with structured output for intelligent decision
    model = get_chat_model()
    structured = model.with_structured_output(AlertDecision)

    # Create prompt for alert decision
    system_prompt = """You are an intelligent DevOps alert decision system for Kubernetes.

Your task is to decide whether a human should be alerted via Slack about this anomaly.

Consider these factors:
- Severity: CRITICAL anomalies always need alerts
- Confidence: Low confidence (<0.7) may need human verification
- Blast radius: WIDE impact requires immediate attention
- Auto-execution: Successful auto-heals reduce alert priority
- Execution failure: Failed remediation attempts need alerts
- Human involvement: Rejected plans or HITL approvals may need follow-up

Alert if:
- CRITICAL severity anomaly
- HIGH severity + LOW confidence (<0.6)
- MEDIUM severity + WIDE blast radius
- Execution failed or was rejected
- High-risk changes that weren't auto-executed

Don't alert if:
- LOW severity issues
- Successful auto-remediation of minor issues
- Normal operations or informational events

Provide a clear reason for your decision."""

    try:
        human_msg = HumanMessage(content=json.dumps(context, default=str)[:50_000])
        decision = structured.invoke([SystemMessage(content=system_prompt), human_msg])

        log.info("Alert decision: %s (%s)", decision.should_alert, decision.reason)

        return {
            "should_alert": decision.should_alert,
            "alert_reason": decision.reason
        }

    except Exception as e:
        log.warning("Alert decision LLM failed: %s, defaulting to alert", e)
        # Default to alerting on LLM failure for safety
        return {
            "should_alert": True,
            "alert_reason": f"Decision system error: {e}, alerting for safety"
        }