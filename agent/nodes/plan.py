from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agent.rule_engine import generate_plan_for_anomaly
from schemas.models import RemediationPlan
from agent.llm_factory import get_chat_model
from agent.prompts_util import load_prompt
from agent.state import AgentState
from utils.structured_logger import get_logger

log = get_logger(__name__)


def _fallback_plan(primary: dict, diagnosis: str) -> RemediationPlan:
    """Deterministic safe plan when LLM is unavailable."""
    at = AnomalyType(primary["type"])
    ar_dict = primary["affected_resource"]
    from schemas.models import AffectedResource

    ar = AffectedResource.model_validate(ar_dict)

    if at == AnomalyType.NODE_NOT_READY or at == AnomalyType.DEPLOYMENT_STALLED:
        return RemediationPlan(
            action=ActionType.ALERT_HUMAN,
            target=ar,
            parameters={"reason": "HITL-only anomaly"},
            confidence=0.7,
            blast_radius=BlastRadius.HIGH,
            rationale=diagnosis[:500],
        )
    if at == AnomalyType.IMAGE_PULL_BACK_OFF:
        return RemediationPlan(
            action=ActionType.ALERT_HUMAN,
            target=ar,
            parameters={"reason": "Image pull failure"},
            confidence=0.75,
            blast_radius=BlastRadius.MEDIUM,
            rationale=diagnosis[:500],
        )
    if at == AnomalyType.OOM_KILLED:
        return RemediationPlan(
            action=ActionType.PATCH_RESOURCE_LIMITS,
            target=ar,
            parameters={"bump_memory_pct": 0.5},
            confidence=0.85,
            blast_radius=BlastRadius.LOW,
            rationale="Increase memory limits then restart workload.",
        )
    if at == AnomalyType.EVICTED_POD:
        return RemediationPlan(
            action=ActionType.DELETE_POD,
            target=ar,
            parameters={"reason": "remove evicted pod"},
            confidence=0.85,
            blast_radius=BlastRadius.LOW,
            rationale="Delete evicted pod so it can be rescheduled.",
        )
    return RemediationPlan(
        action=ActionType.RESTART_POD,
        target=ar,
        parameters={},
        confidence=0.85,
        blast_radius=BlastRadius.LOW,
        rationale="Restart failing pod.",
    )


def plan_node(state: AgentState) -> dict[str, Any]:
    primary = state.get("primary_anomaly")
    if not primary:
        return {"plan": None}

    diagnosis = state.get("diagnosis") or ""

    # Try rule-based planning first
    plan = generate_plan_for_anomaly(primary)
    if plan is not None:
        log.info("Using rule-based plan: action=%s blast=%s", plan.action, plan.blast_radius)
        return {"plan": plan.model_dump(mode="json")}

    # Fallback to LLM planning
    log.info("No rule-based plan found, using LLM planning")
    model = get_chat_model()
    structured = model.with_structured_output(RemediationPlan)
    sys = load_prompt("plan_system.txt")
    msg = HumanMessage(
        content=json.dumps({"anomaly": primary, "diagnosis": diagnosis, "evidence": state.get("evidence_list") or []})
    )
    try:
        plan: RemediationPlan | None = structured.invoke([SystemMessage(content=sys), msg])
    except Exception as e:
        log.warning("plan LLM failed, using fallback: %s", e)
        plan = _fallback_plan(primary, diagnosis)
    if plan is None:
        plan = _fallback_plan(primary, diagnosis)

    log.info("Plan: action=%s blast=%s", plan.action, plan.blast_radius)
    return {"plan": plan.model_dump(mode="json")}
