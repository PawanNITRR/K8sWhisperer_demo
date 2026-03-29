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
        # More realistic mock logs that simulate common Kubernetes issues
        return """2026-03-30 00:54:00,123 INFO Starting application server on port 8080
2026-03-30 00:54:01,456 INFO Database connection established
2026-03-30 00:54:02,789 INFO Loading configuration from /app/config.yaml
2026-03-30 00:54:03,012 ERROR Failed to connect to redis service: Connection refused
2026-03-30 00:54:03,123 WARN Retrying database connection in 5 seconds
2026-03-30 00:54:08,456 ERROR Database connection timeout after 3 attempts
2026-03-30 00:54:08,567 FATAL Application startup failed: Unable to establish required connections
2026-03-30 00:54:08,678 INFO Shutting down gracefully...
2026-03-30 00:54:08,789 ERROR java.lang.RuntimeException: Service unavailable
        at com.example.App.start(App.java:45)
        at com.example.Main.main(Main.java:12)
2026-03-30 00:54:08,890 INFO Process terminated with exit code 1"""

    def get_pod_json(self, namespace: str, name: str) -> dict[str, Any]:
        return {"metadata": {"name": name}}

    def delete_pod(self, namespace: str, name: str) -> str:
        return f"Mock deleted pod {namespace}/{name}"

    def patch_deployment(self, namespace: str, name: str, patch: dict[str, Any]) -> str:
        return "Mock patch applied"

    def rollout_status_relaxed(self, namespace: str, deployment: str):
        return 0, "Mock rollout successful"