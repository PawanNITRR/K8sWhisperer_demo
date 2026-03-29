from __future__ import annotations

from typing import Any

from schemas.enums import ActionType, AnomalyType, BlastRadius
from schemas.models import AffectedResource, RemediationPlan
from utils.structured_logger import get_logger

log = get_logger(__name__)


def generate_plan_for_anomaly(anomaly: dict[str, Any]) -> RemediationPlan | None:
    """
    Generate deterministic remediation plan based on anomaly type.
    Returns None if no rule matches (fallback to LLM).
    """
    anomaly_type = AnomalyType(anomaly["type"])
    affected_resource = AffectedResource.model_validate(anomaly["affected_resource"])

    log.info("Rule-based plan selected for anomaly: %s", anomaly_type.value)

    if anomaly_type == AnomalyType.CRASH_LOOP_BACK_OFF:
        return RemediationPlan(
            action=ActionType.RESTART_POD,
            target=affected_resource,
            parameters={},
            confidence=0.9,
            blast_radius=BlastRadius.LOW,
            rationale="Pod in CrashLoopBackOff - restart to recover from application failure."
        )

    elif anomaly_type == AnomalyType.OOM_KILLED:
        return RemediationPlan(
            action=ActionType.PATCH_RESOURCE_LIMITS,
            target=affected_resource,
            parameters={"bump_memory_pct": 0.5},
            confidence=0.85,
            blast_radius=BlastRadius.LOW,
            rationale="Pod killed due to OOM - increase memory limits by 50% and restart."
        )

    elif anomaly_type == AnomalyType.PENDING_POD:
        return RemediationPlan(
            action=ActionType.ALERT_HUMAN,
            target=affected_resource,
            parameters={"reason": "Pod stuck in Pending - check node capacity and scheduling constraints"},
            confidence=0.8,
            blast_radius=BlastRadius.MEDIUM,
            rationale="Pod pending for >5 minutes - requires human investigation of scheduling issues."
        )

    elif anomaly_type == AnomalyType.IMAGE_PULL_BACK_OFF:
        return RemediationPlan(
            action=ActionType.ALERT_HUMAN,
            target=affected_resource,
            parameters={"reason": "Image pull failure - check image registry access and credentials"},
            confidence=0.9,
            blast_radius=BlastRadius.LOW,
            rationale="Container cannot pull image - human intervention required for image/registry issues."
        )

    elif anomaly_type == AnomalyType.CPU_THROTTLING:
        return RemediationPlan(
            action=ActionType.PATCH_RESOURCE_LIMITS,
            target=affected_resource,
            parameters={"bump_cpu_pct": 0.5},
            confidence=0.8,
            blast_radius=BlastRadius.MEDIUM,
            rationale="CPU throttling detected - increase CPU limits by 50%."
        )

    elif anomaly_type == AnomalyType.EVICTED_POD:
        return RemediationPlan(
            action=ActionType.DELETE_POD,
            target=affected_resource,
            parameters={"reason": "Pod was evicted due to resource pressure"},
            confidence=0.9,
            blast_radius=BlastRadius.LOW,
            rationale="Pod evicted - delete to allow rescheduling on available node."
        )

    elif anomaly_type == AnomalyType.DEPLOYMENT_STALLED:
        return RemediationPlan(
            action=ActionType.ALERT_HUMAN,
            target=affected_resource,
            parameters={"reason": "Deployment rollout stalled - check events and decide rollback/force"},
            confidence=0.85,
            blast_radius=BlastRadius.HIGH,
            rationale="Deployment not progressing - requires human decision on rollback or force rollout."
        )

    elif anomaly_type == AnomalyType.NODE_NOT_READY:
        return RemediationPlan(
            action=ActionType.ALERT_HUMAN,
            target=affected_resource,
            parameters={"reason": "Node not ready - investigate hardware/network issues, never auto-drain"},
            confidence=0.95,
            blast_radius=BlastRadius.CRITICAL,
            rationale="Node failure - critical infrastructure issue requiring immediate human attention."
        )

    # No rule matches - return None for LLM fallback
    log.info("No rule-based plan for anomaly type: %s", anomaly_type.value)
    return None


def detect_cpu_throttling(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect CPU throttling from Prometheus metrics.
    Returns list of anomaly dictionaries.
    """
    anomalies = []
    throttle_data = metrics.get("cpu_throttle_sample", {}).get("data", {}).get("result", [])

    for series in throttle_data:
        metric = series.get("metric", {})
        value = series.get("value", [0, "0"])[1]

        try:
            throttle_rate = float(value)
        except (ValueError, TypeError):
            continue

        # Trigger if throttling rate > 0.5 (50% of time spent throttled)
        if throttle_rate > 0.5:
            namespace = metric.get("namespace", "default")
            pod_name = metric.get("pod", "unknown")

            anomaly = {
                "type": AnomalyType.CPU_THROTTLING.value,
                "severity": "MEDIUM",
                "affected_resource": {
                    "kind": "Pod",
                    "namespace": namespace,
                    "name": pod_name
                },
                "confidence": min(0.95, 0.7 + throttle_rate),
                "trigger_signal": f"cpu_throttled={throttle_rate:.3f}",
                "notes": f"Pod experiencing CPU throttling at rate {throttle_rate}"
            }
            anomalies.append(anomaly)

    return anomalies