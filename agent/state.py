from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """
    Shared LangGraph state. Serialized types are plain dicts/lists for checkpoint compatibility.
    """

    # Observe
    events: list[dict[str, Any]]
    cluster: dict[str, Any]

    # Detect (replaced each cycle in detect node)
    anomalies: list[dict[str, Any]]
    primary_anomaly: dict[str, Any] | None

    # Diagnose / Plan
    diagnosis: str
    evidence_list: list[str]
    plan: dict[str, Any] | None

    # Safety / execution
    should_auto_execute: bool
    approved: bool | None
    result: str

    # Alert decision
    should_alert: bool
    alert_reason: str

    # Correlation
    cycle_id: str
    graph_thread_id: str
