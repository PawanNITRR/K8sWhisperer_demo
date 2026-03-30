"""Sequential mock-cluster scenarios (one per poll cycle when MOCK_CLUSTER=1)."""

from __future__ import annotations

# Rotates after each full LangGraph run (see main.py).
_MOCK_STATE = {
    "current_index": 0,
    "total_anomalies": 8,
}

# Order must match mcp_servers/kubectl_mock.py and prometheus idx 7 (CPU throttling).
MOCK_SCENARIO_LABELS: list[str] = [
    "CrashLoopBackOff",
    "OOMKilled",
    "PendingPod",
    "EvictedPod",
    "ImagePullBackOff",
    "NodeNotReady",
    "DeploymentStalled",
    "CPUThrottling",
]


def get_current_anomaly_index() -> int:
    return _MOCK_STATE["current_index"]


def get_mock_scenario_label() -> str:
    i = get_current_anomaly_index()
    if 0 <= i < len(MOCK_SCENARIO_LABELS):
        return MOCK_SCENARIO_LABELS[i]
    return f"unknown({i})"


def advance_anomaly() -> None:
    _MOCK_STATE["current_index"] = (_MOCK_STATE["current_index"] + 1) % _MOCK_STATE["total_anomalies"]
