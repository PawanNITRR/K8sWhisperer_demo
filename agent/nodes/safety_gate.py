from __future__ import annotations

from schemas.constants import DESTRUCTIVE_ACTIONS, HITL_ONLY_ANOMALIES, SAFETY_CONFIDENCE_THRESHOLD
from schemas.enums import AnomalyType, BlastRadius, Severity
from schemas.models import RemediationPlan


def should_auto_execute(plan: RemediationPlan, anomaly_type: AnomalyType, anomaly_severity: Severity) -> bool:
    """
    Enhanced safety gate with severity-based rules:
    - CRITICAL: Never auto-execute
    - HIGH: Auto-execute only if confidence > threshold and blast radius LOW
    - MEDIUM: Require approval unless confidence very high
    - LOW: Allow auto-execute
    """
    # CRITICAL anomalies always require human approval
    if anomaly_severity == Severity.CRITICAL:
        return False

    # HITL-only anomalies (defined in constants)
    if anomaly_type in HITL_ONLY_ANOMALIES:
        return False

    # Destructive actions never auto-execute
    if plan.action in DESTRUCTIVE_ACTIONS:
        return False

    # Confidence threshold check
    if plan.confidence <= SAFETY_CONFIDENCE_THRESHOLD:
        return False

    # Blast radius check - only LOW blast radius allowed for auto-execution
    if plan.blast_radius != BlastRadius.LOW:
        return False

    # For HIGH severity, be more restrictive
    if anomaly_severity == Severity.HIGH and plan.confidence < 0.9:
        return False

    # For MEDIUM severity, require even higher confidence
    if anomaly_severity == Severity.MEDIUM and plan.confidence < 0.95:
        return False

    return True


def safety_gate_node(state: dict) -> dict:
    plan_raw = state.get("plan")
    primary = state.get("primary_anomaly")
    if not plan_raw or not primary:
        return {"should_auto_execute": False}

    plan = RemediationPlan.model_validate(plan_raw)
    at = AnomalyType(primary["type"])
    severity = Severity(primary.get("severity", "LOW"))
    auto = should_auto_execute(plan, at, severity)
    return {"should_auto_execute": auto}
