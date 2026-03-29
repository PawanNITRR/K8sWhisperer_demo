from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from schemas.enums import AnomalyType, Severity
from schemas.models import AffectedResource, Anomaly


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def detect_from_pod_items(items: list[dict[str, Any]], now: datetime | None = None) -> list[Anomaly]:
    """
    Deterministic signals from pod JSON (complements LLM classifier).
    """
    now = now or datetime.now(timezone.utc)
    out: list[Anomaly] = []
    for pod in items:
        meta = pod.get("metadata") or {}
        ns = meta.get("namespace") or "default"
        name = meta.get("name") or "unknown"
        status = pod.get("status") or {}
        phase = status.get("phase") or ""
        reason = status.get("reason") or ""

        ar = AffectedResource(namespace=ns, name=name, kind="Pod")

        if reason == "Evicted":
            out.append(
                Anomaly(
                    type=AnomalyType.EVICTED_POD,
                    severity=Severity.LOW,
                    affected_resource=ar,
                    confidence=0.95,
                    trigger_signal="pod.status.reason=Evicted",
                )
            )

        if phase == "Pending":
            ts = _parse_ts(meta.get("creationTimestamp"))
            if ts and (now - ts).total_seconds() > 300:
                out.append(
                    Anomaly(
                        type=AnomalyType.PENDING_POD,
                        severity=Severity.MEDIUM,
                        affected_resource=ar,
                        confidence=0.85,
                        trigger_signal="Pending > 5m",
                    )
                )

        for cs in status.get("containerStatuses") or []:
            st = cs.get("state") or {}
            waiting = st.get("waiting") or {}
            wr = waiting.get("reason") or ""
            if wr == "CrashLoopBackOff":
                rc = int(cs.get("restartCount") or 0)
                if rc > 3:
                    out.append(
                        Anomaly(
                            type=AnomalyType.CRASH_LOOP_BACK_OFF,
                            severity=Severity.HIGH,
                            affected_resource=ar,
                            confidence=min(0.99, 0.6 + rc / 20),
                            trigger_signal=f"CrashLoopBackOff restartCount={rc}",
                        )
                    )
            if wr == "ImagePullBackOff":
                out.append(
                    Anomaly(
                        type=AnomalyType.IMAGE_PULL_BACK_OFF,
                        severity=Severity.MEDIUM,
                        affected_resource=ar,
                        confidence=0.9,
                        trigger_signal="ImagePullBackOff",
                    )
                )
            term = (cs.get("lastState") or {}).get("terminated") or {}
            if term.get("reason") == "OOMKilled":
                out.append(
                    Anomaly(
                        type=AnomalyType.OOM_KILLED,
                        severity=Severity.HIGH,
                        affected_resource=ar,
                        confidence=0.95,
                        trigger_signal="lastState.terminated.reason=OOMKilled",
                    )
                )

    return out


def detect_from_nodes(items: list[dict[str, Any]]) -> list[Anomaly]:
    out: list[Anomaly] = []
    for node in items:
        meta = node.get("metadata") or {}
        name = meta.get("name") or "unknown"
        for cond in node.get("status", {}).get("conditions") or []:
            if cond.get("type") == "Ready" and cond.get("status") == "False":
                ar = AffectedResource(kind="Node", namespace="", name=name, api_version="v1")
                out.append(
                    Anomaly(
                        type=AnomalyType.NODE_NOT_READY,
                        severity=Severity.CRITICAL,
                        affected_resource=ar,
                        confidence=0.95,
                        trigger_signal="Node Ready=False",
                    )
                )
    return out


def detect_deployment_stalled(items: list[dict[str, Any]], now: datetime | None = None) -> list[Anomaly]:
    now = now or datetime.now(timezone.utc)
    out: list[Anomaly] = []
    for dep in items:
        meta = dep.get("metadata") or {}
        ns = meta.get("namespace") or "default"
        dep_name = meta.get("name") or "unknown"
        spec = dep.get("spec") or {}
        st = dep.get("status") or {}
        replicas = int(spec.get("replicas") or 0)
        updated = int(st.get("updatedReplicas") or 0)
        if replicas <= 0:
            continue
        if updated == replicas:
            continue
        stale_since: datetime | None = None
        for cond in st.get("conditions") or []:
            if cond.get("type") == "Progressing":
                stale_since = _parse_ts(cond.get("lastTransitionTime"))
                break
        if stale_since is None:
            stale_since = _parse_ts(meta.get("creationTimestamp"))
        if stale_since is None:
            continue
        if (now - stale_since).total_seconds() <= 600:
            continue
        ar = AffectedResource(kind="Deployment", namespace=ns, name=dep_name, api_version="apps/v1")
        out.append(
            Anomaly(
                type=AnomalyType.DEPLOYMENT_STALLED,
                severity=Severity.HIGH,
                affected_resource=ar,
                confidence=0.8,
                trigger_signal="updatedReplicas != replicas for >10m",
            )
        )
    return out
