from __future__ import annotations

import json
from typing import Any

from mcp_servers.base_mcp import BaseMCP
from config import get_settings


class KubectlMCP(BaseMCP):
    def __init__(self):
        super().__init__("kubectl-mcp")

    # ---------- BASIC RUN ----------
    def run(self, args: list[str]) -> str:
        return self.run_cmd(["kubectl"] + args)

    # ---------- GETTERS ----------
    def get_events_all_namespaces(self) -> list[dict[str, Any]]:
        out = self.run(["get", "events", "-A", "-o", "json"])
        return json.loads(out).get("items", [])

    def get_pods_all_namespaces(self) -> list[dict[str, Any]]:
        out = self.run(["get", "pods", "-A", "-o", "json"])
        return json.loads(out).get("items", [])

    def get_nodes(self) -> list[dict[str, Any]]:
        out = self.run(["get", "nodes", "-o", "json"])
        return json.loads(out).get("items", [])

    def get_deployments_all_namespaces(self) -> list[dict[str, Any]]:
        out = self.run(["get", "deployments", "-A", "-o", "json"])
        return json.loads(out).get("items", [])

    def get_pod_json(self, namespace: str, name: str) -> dict[str, Any]:
        out = self.run(["get", "pod", name, "-n", namespace, "-o", "json"])
        return json.loads(out)

    # ---------- DESCRIBE ----------
    def describe_pod(self, namespace: str, name: str) -> str:
        return self.run(["describe", "pod", name, "-n", namespace])

    def describe_deployment(self, namespace: str, name: str) -> str:
        return self.run(["describe", "deployment", name, "-n", namespace])

    # ---------- LOGS ----------
    def logs_pod(self, namespace: str, name: str, tail: int = 100) -> str:
        return self.run(
            ["logs", name, "-n", namespace, f"--tail={tail}"]
        )

    # ---------- ACTIONS ----------
    def delete_pod(self, namespace: str, name: str) -> str:
        return self.run(["delete", "pod", name, "-n", namespace])

    def patch_deployment(self, namespace: str, name: str, patch: dict[str, Any]) -> str:
        return self.run(
            [
                "patch",
                "deployment",
                name,
                "-n",
                namespace,
                "--type=merge",
                "-p",
                json.dumps(patch),
            ]
        )

    # ---------- ROLLOUT ----------
    def rollout_status_relaxed(self, namespace: str, deployment: str) -> tuple[int, str]:
        try:
            out = self.run(
                ["rollout", "status", f"deployment/{deployment}", "-n", namespace]
            )
            return 0, out
        except Exception as e:
            return 1, str(e)


# ---------- SINGLETON ----------
_kubectl_client: KubectlMCP | None = None


def get_kubectl_client():
    global _kubectl_client
    if _kubectl_client is None:
        settings = get_settings()
        if settings.mock_cluster:
            from mcp_servers.kubectl_mock import KubectlMock
            _kubectl_client = KubectlMock()
        else:
            _kubectl_client = KubectlMCP()
    return _kubectl_client