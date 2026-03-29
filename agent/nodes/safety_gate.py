from __future__ import annotations

from schemas.constants import DESTRUCTIVE_ACTIONS, HITL_ONLY_ANOMALIES, SAFETY_CONFIDENCE_THRESHOLD
from schemas.enums import AnomalyType, BlastRadius
from schemas.models import RemediationPlan


def should_auto_execute(plan: RemediationPlan, anomaly_type: AnomalyType) -> bool:
    """
    Pure safety gate: no LLM calls. Returns True only when auto-execution is permitted.
    """
    if anomaly_type in HITL_ONLY_ANOMALIES:
        return False
    if plan.action in DESTRUCTIVE_ACTIONS:
        return False
    if plan.confidence <= SAFETY_CONFIDENCE_THRESHOLD:
        return False
    if plan.blast_radius != BlastRadius.LOW:
        return False
    return True


def safety_gate_node(state: dict) -> dict:
    plan_raw = state.get("plan")
    primary = state.get("primary_anomaly")
    if not plan_raw or not primary:
        return {"should_auto_execute": False}

    plan = RemediationPlan.model_validate(plan_raw)
    at = AnomalyType(primary["type"])
    auto = should_auto_execute(plan, at)
    return {"should_auto_execute": auto}
