from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from schemas.enums import AnomalyType, Severity
from schemas.models import Anomaly
from agent.llm_factory import get_chat_model
from agent.prompts_util import load_prompt
from agent.rollout_guard import pod_has_rollout_in_progress
from agent.rule_detector import (
    detect_deployment_stalled,
    detect_from_nodes,
    detect_from_pod_items,
)
from agent.rule_engine import detect_cpu_throttling
from agent.state import AgentState
from mcp_servers.kubectl_mcp import get_kubectl_client
from utils.structured_logger import get_logger

log = get_logger(__name__)


class DetectLLMResult(BaseModel):
    anomalies: list[Anomaly] = Field(default_factory=list)


def _dedupe(anomalies: list[Anomaly]) -> list[Anomaly]:
    seen: set[tuple[str, str, str]] = set()
    out: list[Anomaly] = []
    for a in anomalies:
        key = (a.affected_resource.namespace, a.affected_resource.name, a.type.value)
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


def _severity_rank(sev: Severity) -> int:
    order = {
        Severity.CRITICAL: 0,
        Severity.HIGH: 1,
        Severity.MEDIUM: 2,
        Severity.LOW: 3,
    }
    return order.get(sev, 9)


def pick_primary(anomalies: list[Anomaly]) -> Anomaly | None:
    if not anomalies:
        return None
    return sorted(anomalies, key=lambda a: (_severity_rank(a.severity), -a.confidence))[0]


def detect_node(state: AgentState) -> dict[str, Any]:
    cluster = state.get("cluster") or {}
    pods = cluster.get("pods_summary")
    nodes = cluster.get("nodes_summary")
    deps = cluster.get("deployments_summary")
    events = cluster.get("events")
    if not isinstance(pods, list):
        pods = []
    if not isinstance(nodes, list):
        nodes = []
    if not isinstance(deps, list):
        deps = []
    if not isinstance(events, list):
        events = []

    rule_based: list[Anomaly] = []
    rule_based.extend(detect_from_pod_items(pods))
    rule_based.extend(detect_from_nodes(nodes))
    rule_based.extend(detect_deployment_stalled(deps))

    # Add CPU throttling detection from Prometheus metrics
    prom_metrics = cluster.get("prometheus_snippets", {})
    cpu_anomalies = detect_cpu_throttling(prom_metrics)
    for anomaly_dict in cpu_anomalies:
        anomaly = Anomaly.model_validate(anomaly_dict)
        rule_based.append(anomaly)

    llm_anomalies: list[Anomaly] = []
    try:
        model = get_chat_model()
        structured = model.with_structured_output(DetectLLMResult)
        sys = load_prompt("detect_system.txt")
        payload = {
            "events": events[-120:],
            "pods": pods[:80],
            "nodes": nodes[:40],
        }
        msg = HumanMessage(content=json.dumps(payload, default=str)[:120_000])
        res: DetectLLMResult | None = structured.invoke(
            [SystemMessage(content=sys), msg],
        )
        if res is None:
            llm_anomalies = []
        else:
            llm_anomalies = list(res.anomalies or [])
    except Exception as e:
        log.warning("LLM detect failed, using rules only: %s", e)

    merged = _dedupe(rule_based + llm_anomalies)

    k = get_kubectl_client()
    filtered: list[Anomaly] = []
    for a in merged:
        if a.type == AnomalyType.CRASH_LOOP_BACK_OFF and a.affected_resource.kind == "Pod":
            try:
                if pod_has_rollout_in_progress(k, a.affected_resource.namespace, a.affected_resource.name):
                    log.info(
                        "Skipping CrashLoop for %s/%s due to likely rollout",
                        a.affected_resource.namespace,
                        a.affected_resource.name,
                    )
                    continue
            except Exception as ex:
                log.debug("rollout guard error: %s", ex)
        filtered.append(a)

    primary = pick_primary(filtered)
    log.info("Detect: %d anomalies (primary=%s)", len(filtered), primary.type if primary else None)

    return {
        "anomalies": [a.model_dump(mode="json") for a in filtered],
        "primary_anomaly": primary.model_dump(mode="json") if primary else None,
    }
