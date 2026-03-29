from __future__ import annotations

import uuid
from typing import Any

from schemas.models import ClusterSnapshot
from mcp_servers.kubectl_mcp import get_kubectl_client
from mcp_servers.prometheus_mcp import PrometheusMCP
from utils.structured_logger import get_logger

from agent.state import AgentState

log = get_logger(__name__)

MAX_EVENTS = 250


def observe_node(state: AgentState) -> dict[str, Any]:
    """
    Poll cluster via kubectl (MCP-style adapter), normalize into ClusterSnapshot, reset per-cycle fields.
    """
    k = get_kubectl_client()
    events = k.get_events_all_namespaces()
    events = events[-MAX_EVENTS:] if len(events) > MAX_EVENTS else events
    pods = k.get_pods_all_namespaces()
    nodes = k.get_nodes()
    deps = k.get_deployments_all_namespaces()

    prom: dict[str, Any] = {}
    pm = PrometheusMCP()
    if pm.health().get("ok"):
        try:
            prom["cpu_throttle_sample"] = pm.query(
                "sum(rate(container_cpu_cfs_throttled_seconds_total[5m])) by (namespace,pod)"
            )
        except Exception as e:
            prom["error"] = str(e)

    snap = ClusterSnapshot(
        events=events,
        pods_summary=pods,
        nodes_summary=nodes,
        deployments_summary=deps,
        prometheus_snippets=prom,
        raw={"observe_version": 1},
    )

    cycle_id = str(uuid.uuid4())
    log.info("Observe cycle %s: events=%d pods=%d nodes=%d", cycle_id, len(events), len(pods), len(nodes))

    return {
        "events": events,
        "cluster": snap.model_dump(mode="json"),
        "anomalies": [],
        "primary_anomaly": None,
        "diagnosis": "",
        "evidence_list": [],
        "plan": None,
        "should_auto_execute": False,
        "approved": None,
        "result": "",
        "cycle_id": cycle_id,
    }
