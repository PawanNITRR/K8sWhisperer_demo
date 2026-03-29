from __future__ import annotations

import json
from typing import Any

from mcp_servers.base_mcp import BaseMCP


class MockKubectlMCP(BaseMCP):
    """
    In-memory cluster fixture for running the pipeline without a real kube-apiserver.
    Simulates one CrashLoopBackOff pod and a parent Deployment for diagnose/execute paths.
    """

    name = "kubectl-mock"

    _ns = "default"
    _pod = "demo-crashloop-abc12"
    _rs = "demo-workload-7d4f8"
    _dep = "demo-workload"

    def health(self) -> dict:
        return {
            "ok": True,
            "clientVersion": {"gitVersion": "mock"},
            "serverVersion": {"gitVersion": "mock"},
        }

    def run(self, args: list[str], *, input_text: str | None = None) -> str:
        joined = " ".join(args)
        if len(args) >= 6 and args[0] == "get" and args[1] in ("rs", "replicaset") and args[-1] == "json":
            return json.dumps(
                {
                    "metadata": {
                        "namespace": self._ns,
                        "name": self._rs,
                        "ownerReferences": [{"kind": "Deployment", "name": self._dep}],
                    }
                }
            )
        if len(args) >= 6 and args[0] == "get" and args[1] == "deployment" and args[-1] == "json":
            return json.dumps(
                {
                    "spec": {
                        "template": {
                            "spec": {
                                "containers": [
                                    {
                                        "name": "app",
                                        "resources": {
                                            "limits": {"memory": "128Mi"},
                                            "requests": {"memory": "64Mi"},
                                        },
                                    }
                                ]
                            }
                        }
                    }
                }
            )
        if len(args) >= 2 and args[0] == "rollout" and args[1] == "restart":
            return "deployment restarted (mock)"
        if args[:2] == ["delete", "pod"]:
            return f'pod "{self._pod}" deleted (mock)'
        raise RuntimeError(f"MockKubectlMCP: unsupported kubectl invocation: {joined}")

    def run_allow_fail(self, args: list[str]) -> tuple[int, str]:
        joined = " ".join(args)
        if "rollout status" in joined:
            return 0, "deployment demo-workload successfully rolled out (mock)"
        return 0, "(mock)"

    def get_events_all_namespaces(self) -> list[dict[str, Any]]:
        return []

    def get_pods_all_namespaces(self) -> list[dict[str, Any]]:
        return [self._crash_pod_item()]

    def get_nodes(self) -> list[dict[str, Any]]:
        return [
            {
                "metadata": {"name": "mock-node"},
                "status": {
                    "conditions": [{"type": "Ready", "status": "True"}],
                },
            }
        ]

    def get_deployments_all_namespaces(self) -> list[dict[str, Any]]:
        return [
            {
                "metadata": {"namespace": self._ns, "name": self._dep, "creationTimestamp": "2020-01-01T00:00:00Z"},
                "spec": {"replicas": 1},
                "status": {"updatedReplicas": 1, "replicas": 1, "conditions": []},
            }
        ]

    def describe_pod(self, namespace: str, name: str) -> str:
        return f"Name: {name}\nNamespace: {namespace}\nState: CrashLoopBackOff (mock describe)"

    def describe_deployment(self, namespace: str, name: str) -> str:
        return f"Name: {name}\nReplicas: 1 updated, 1 total (mock describe)"

    def logs_pod(self, namespace: str, name: str, tail: int = 200) -> str:
        return "Error: application exited with code 1\nmock stack trace line\nOOM? no\n"

    def rollout_status(self, namespace: str, deployment_name: str) -> str:
        return "deployment demo-workload successfully rolled out (mock)"

    def rollout_status_relaxed(self, namespace: str, deployment_name: str) -> tuple[int, str]:
        return 0, "deployment demo-workload successfully rolled out (mock)"

    def delete_pod(self, namespace: str, name: str) -> str:
        return f'pod "{name}" deleted (mock)'

    def patch_pod(self, namespace: str, name: str, patch: dict[str, Any]) -> str:
        return "pod patched (mock)"

    def patch_deployment(self, namespace: str, name: str, patch: dict[str, Any]) -> str:
        return "deployment patched (mock)"

    def get_pod_json(self, namespace: str, name: str) -> dict[str, Any]:
        return self._crash_pod_item()

    def _crash_pod_item(self) -> dict[str, Any]:
        return {
            "metadata": {
                "namespace": self._ns,
                "name": self._pod,
                "creationTimestamp": "2020-01-01T00:00:00Z",
                "ownerReferences": [{"kind": "ReplicaSet", "name": self._rs}],
            },
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {
                        "name": "app",
                        "restartCount": 6,
                        "state": {"waiting": {"reason": "CrashLoopBackOff"}},
                    }
                ],
            },
        }
