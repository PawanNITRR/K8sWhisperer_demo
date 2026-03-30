"""Thread id + LangGraph snapshot helpers for the dashboard GET /state API."""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any

_lock = threading.Lock()
_active_thread_id: str | None = None


def set_active_thread_id(thread_id: str) -> None:
    global _active_thread_id
    with _lock:
        _active_thread_id = thread_id


def get_active_thread_id() -> str | None:
    with _lock:
        return _active_thread_id


def _normalize_next(raw_next: Any) -> list[str]:
    if not raw_next:
        return []
    out: list[str] = []
    for item in raw_next:
        if isinstance(item, str):
            out.append(item)
            continue
        if hasattr(item, "node") and isinstance(getattr(item, "node"), str):
            out.append(getattr(item, "node"))
            continue
        if hasattr(item, "name") and isinstance(getattr(item, "name"), str):
            out.append(getattr(item, "name"))
            continue
        out.append(str(item))
    return out


def _infer_current_node(snap: Any, values: dict[str, Any]) -> str:
    intr = getattr(snap, "interrupts", None)
    if intr:
        return "hitl"

    nxt = _normalize_next(getattr(snap, "next", None))
    if not nxt:
        return "explain"

    first = nxt[0].lower() if isinstance(nxt[0], str) else str(nxt[0]).lower()
    if "hitl" in first:
        return "hitl"
    return nxt[0] if isinstance(nxt[0], str) else str(nxt[0])


def _pods_from_cluster(cluster: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not cluster:
        return []
    raw = cluster.get("pods_summary") or []
    out: list[dict[str, Any]] = []
    for p in raw:
        if not isinstance(p, dict):
            continue
        meta = p.get("metadata") or {}
        name = meta.get("name", "unknown")
        ns = meta.get("namespace", "default")
        status_obj = p.get("status") or {}
        phase = status_obj.get("phase", "Unknown")
        restarts = 0
        for cs in status_obj.get("containerStatuses") or []:
            if isinstance(cs, dict):
                restarts += int(cs.get("restartCount") or 0)

        display = phase
        for cs in status_obj.get("containerStatuses") or []:
            if not isinstance(cs, dict):
                continue
            waiting = (cs.get("state") or {}).get("waiting") or {}
            if isinstance(waiting, dict) and waiting.get("reason"):
                display = waiting["reason"]
                break
            last_t = (cs.get("lastState") or {}).get("terminated") or {}
            if isinstance(last_t, dict) and last_t.get("reason"):
                display = last_t["reason"]
                break
        if status_obj.get("reason") and phase == "Failed":
            display = status_obj.get("reason")

        spec = p.get("spec") or {}
        containers = spec.get("containers") or []
        img = "—"
        if containers and isinstance(containers[0], dict):
            img = containers[0].get("image") or "—"

        out.append(
            {
                "name": f"{ns}/{name}",
                "status": display,
                "image": img,
                "restarts": restarts,
            }
        )
    return out


def _clean_anomaly_label(s: str) -> str:
    """Remove standalone 'cluster' from UI anomaly text; collapse whitespace."""
    t = re.sub(r"\bcluster\b", "", s, flags=re.IGNORECASE)
    t = " ".join(t.split()).strip()
    return t if t else "—"


def _audit_rows_for_ui(entries: list[Any]) -> list[dict[str, Any]]:
    # Demo table mapping (matches the screenshot you sent).
    # We prefer this mapping because older audit_log.json rows may not include
    # the newer structured fields (`anomaly_type`, `planned_action`).
    demo_auto_action_by_anomaly: dict[str, str] = {
        "CrashLoopBackOff": "Fetch logs -> diagnose -> auto restart pod",
        "OOMKilled": "Read limits -> patch +50% memory -> restart",
        "PendingPod": "Describe -> check node capacity -> recommend",
        "ImagePullBackOff": "Extract image -> alert human",
        "CPUThrottling": "Patch CPU limit upward -> verify throttle drops",
        "EvictedPod": "Check node pressure -> delete evicted pod",
        "DeploymentStalled": "Check events -> HITL: rollback or force rollout",
        "NodeNotReady": "Log metrics -> HITL only -> never auto-drain",
    }

    known_anomalies = list(demo_auto_action_by_anomaly.keys())
    # Example of mock summary text:
    #   [MOCK_CLUSTER] Anomaly CrashLoopBackOff (sev=high). Diagnosis: ...
    anomaly_regex = re.compile(r"\b(" + "|".join(map(re.escape, known_anomalies)) + r")\b")

    rows: list[dict[str, Any]] = []
    for e in entries[-200:]:
        if not isinstance(e, dict):
            continue

        raw_res = (e.get("resource_ref") or e.get("resource") or "").strip()
        resource = raw_res if raw_res and raw_res.lower() != "cluster" else "—"

        # 1) Prefer the newer structured field if present
        anomaly = e.get("anomaly_type")
        anomaly_str: str | None = str(anomaly) if anomaly else None

        # 2) Otherwise try to extract anomaly type from the summary text (works for MOCK_CLUSTER)
        if not anomaly_str:
            summary_text = e.get("summary") or ""
            m = anomaly_regex.search(str(summary_text))
            if m:
                anomaly_str = m.group(1)

        # 3) Final fallback
        if not anomaly_str:
            anomaly_str = str((e.get("phase") or "record")).upper()
        if anomaly_str.strip().lower() == "cluster":
            anomaly_str = "—"

        planned = e.get("planned_action")
        planned_s = str(planned) if planned else None

        map_key = anomaly_str if anomaly_str != "—" else None

        # Action column:
        # - if we know the anomaly, show the screenshot's "Auto-Action" string
        # - else fall back to planned/plaint text
        if map_key and map_key in demo_auto_action_by_anomaly:
            action_s = demo_auto_action_by_anomaly[map_key]
        elif map_key:
            cleaned_key = _clean_anomaly_label(map_key)
            if cleaned_key in demo_auto_action_by_anomaly:
                action_s = demo_auto_action_by_anomaly[cleaned_key]
            elif planned_s and resource != "—":
                action_s = f"{planned_s} -> {resource}"
            elif planned_s:
                action_s = planned_s
            else:
                raw = e.get("action_taken")
                action_s = (raw[:160] if isinstance(raw, str) else None) or "—"
        elif planned_s and resource != "—":
            action_s = f"{planned_s} -> {resource}"
        elif planned_s:
            action_s = planned_s
        else:
            raw = e.get("action_taken")
            action_s = (raw[:160] if isinstance(raw, str) else None) or "—"

        anomaly_display = anomaly_str if anomaly_str == "—" else _clean_anomaly_label(anomaly_str)

        rows.append(
            {
                "timestamp": e.get("timestamp"),
                "resource": resource,
                "anomaly_type": anomaly_display,
                "action": action_s,
                "explanation": e.get("summary") or "—",
                "approved": e.get("approved"),
            }
        )
    return rows


def _load_audit_log(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def build_state_payload(graph: Any, settings: Any) -> dict[str, Any]:
    """Shape matches K8sWhisperer dashboard hooks (useCluster)."""
    tid = get_active_thread_id()
    audit_path = Path(settings.audit_log_path)
    audit_raw = _load_audit_log(audit_path)
    audit_log = _audit_rows_for_ui(audit_raw)

    empty: dict[str, Any] = {
        "pods": [],
        "current_node": "observe",
        "plan": None,
        "approved": None,
        "audit_log": audit_log,
        "hitl_thread_id": None,
    }

    if not tid or graph is None:
        return empty

    try:
        snap = graph.get_state({"configurable": {"thread_id": tid}})
    except Exception:
        return empty

    values = snap.values if isinstance(snap.values, dict) else {}
    cluster = values.get("cluster") if isinstance(values.get("cluster"), dict) else {}
    plan = values.get("plan")
    approved = values.get("approved")
    current = _infer_current_node(snap, values)
    intr = getattr(snap, "interrupts", None)

    hitl_thread_id: str | None = None
    if isinstance(plan, dict) and approved is not True and (current == "hitl" or intr):
        hitl_thread_id = tid

    return {
        "pods": _pods_from_cluster(cluster),
        "current_node": current,
        "plan": plan if isinstance(plan, dict) else None,
        "approved": approved,
        "audit_log": audit_log,
        "hitl_thread_id": hitl_thread_id,
    }
