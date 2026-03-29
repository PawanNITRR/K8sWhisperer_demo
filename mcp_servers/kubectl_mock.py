from __future__ import annotations

from typing import Any


class KubectlMock:
    def health(self) -> dict[str, Any]:
        """Return mock health status."""
        return {"ok": True}

    def get_events_all_namespaces(self) -> list[dict[str, Any]]:
        return [{"message": "Mock event: pod crash detected"}]

    def get_pods_all_namespaces(self) -> list[dict[str, Any]]:
        return [{"metadata": {"name": "demo-pod", "namespace": "default"}}]

    def get_nodes(self) -> list[dict[str, Any]]:
        return [{"metadata": {"name": "node-1"}}]

    def get_deployments_all_namespaces(self) -> list[dict[str, Any]]:
        return [{"metadata": {"name": "demo-deployment"}}]

    def describe_pod(self, namespace: str, name: str) -> str:
        return f"Mock describe pod {namespace}/{name}"

    def logs_pod(self, namespace: str, name: str, tail: int = 100) -> str:
        return "Error: CrashLoopBackOff detected"

    def get_pod_json(self, namespace: str, name: str) -> dict[str, Any]:
        return {"metadata": {"name": name}}

    def delete_pod(self, namespace: str, name: str) -> str:
        return f"Mock deleted pod {namespace}/{name}"

    def patch_deployment(self, namespace: str, name: str, patch: dict[str, Any]) -> str:
        return "Mock patch applied"

    def rollout_status_relaxed(self, namespace: str, deployment: str):
        return 0, "Mock rollout successful"