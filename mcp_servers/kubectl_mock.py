from __future__ import annotations

import json
from typing import Any

from utils.mock_state import get_current_anomaly_index
from utils.structured_logger import get_logger

log = get_logger("kubectl-mock")

# ReplicaSet name returned by get rs (owner of workload pods) → infer deployment
_MOCK_RS_NAME = "demo-deployment-7d4f8c9b"
_MOCK_DEPLOYMENT = "demo-deployment"


def _pod_owner_meta() -> dict[str, Any]:
    return {
        "ownerReferences": [
            {
                "apiVersion": "apps/v1",
                "kind": "ReplicaSet",
                "name": _MOCK_RS_NAME,
                "uid": "mock-rs-uid",
                "controller": True,
            }
        ]
    }


def _mock_deployment_doc(namespace: str, name: str) -> dict[str, Any]:
    return {
        "metadata": {"name": name, "namespace": namespace},
        "spec": {
            "replicas": 3,
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "app",
                            "resources": {
                                "limits": {"memory": "512Mi", "cpu": "500m"},
                                "requests": {"memory": "256Mi", "cpu": "250m"},
                            },
                        }
                    ]
                }
            },
        },
        "status": {"updatedReplicas": 3},
    }


def _mock_rs_doc(namespace: str, rs_name: str) -> dict[str, Any]:
    return {
        "metadata": {
            "name": rs_name,
            "namespace": namespace,
            "ownerReferences": [
                {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": _MOCK_DEPLOYMENT,
                }
            ],
        }
    }


class KubectlMock:
    def health(self) -> dict[str, Any]:
        return {"ok": True}

    def run(self, args: list[str]) -> str:
        """Subset of kubectl used by execute_node / infer_deployment_name."""
        a = list(args)
        if len(a) >= 1 and a[0] == "kubectl":
            a = a[1:]
        if not a:
            return ""

        if a[0] == "rollout":
            if len(a) >= 2 and a[1] == "restart":
                return "deployment restarted (mock)"
            if len(a) >= 2 and a[1] == "status":
                return "successfully rolled out (mock)"

        if a[0] == "describe":
            if len(a) >= 3 and a[1] == "node":
                return f"Name:\t{a[2]}\nConditions:\n  Type\tStatus\n  Ready\tUnknown (mock)\n"
            if len(a) >= 3 and a[1] == "deployment":
                return f"Name:\t{a[2]}\nReplicas:\t3 desired | 3 updated | 3 available (mock steady)\n"
            return "Mock describe output."

        if a[0] != "get":
            return "{}"

        try:
            o_i = a.index("-o")
        except ValueError:
            return "{}"
        fmt = a[o_i + 1] if o_i + 1 < len(a) else "json"
        if fmt != "json":
            return "{}"

        kind = a[1]
        ns = "default"
        if "-n" in a:
            ni = a.index("-n")
            ns = a[ni + 1]
        elif "--namespace" in a:
            ni = a.index("--namespace")
            ns = a[ni + 1]

        # kubectl get rs -n NS NAME -o json  OR  get rs NAME -n NS -o json
        if len(a) > 2 and a[2] == "-n":
            name = a[4] if len(a) > 4 else ""
        else:
            name = a[2]

        if kind == "pod":
            return json.dumps(self.get_pod_json(ns, name))
        if kind in ("rs", "replicaset"):
            return json.dumps(_mock_rs_doc(ns, name))
        if kind == "deployment":
            return json.dumps(_mock_deployment_doc(ns, name))

        return "{}"

    def get_events_all_namespaces(self) -> list[dict[str, Any]]:
        idx = get_current_anomaly_index()
        if idx == 0:
            return [{"message": "Mock event: pod crash detected", "involvedObject": {"name": "crashloop-pod"}}]
        if idx == 5:
            return [{"message": "Mock event: node not ready", "involvedObject": {"name": "node-2"}}]
        return []

    def get_pods_all_namespaces(self) -> list[dict[str, Any]]:
        idx = get_current_anomaly_index()
        pods: list[dict[str, Any]] = [
            {
                "metadata": {
                    "name": "frontend-pod",
                    "namespace": "default",
                    "creationTimestamp": "2026-03-30T00:00:00Z",
                },
                "status": {"phase": "Running", "containerStatuses": [{"ready": True, "restartCount": 0}]},
            }
        ]

        def workload_pod(
            name: str,
            created: str,
            status: dict[str, Any],
        ) -> dict[str, Any]:
            meta = {
                "name": name,
                "namespace": "default",
                "creationTimestamp": created,
            }
            meta.update(_pod_owner_meta())
            return {"metadata": meta, "status": status}

        if idx == 0:
            pods.append(
                workload_pod(
                    "crashloop-pod",
                    "2026-03-30T00:00:00Z",
                    {
                        "phase": "Running",
                        "containerStatuses": [
                            {
                                "name": "app",
                                "restartCount": 15,
                                "state": {"waiting": {"reason": "CrashLoopBackOff", "message": "back-off 5m0s restarting"}},
                            }
                        ],
                    },
                )
            )
        elif idx == 1:
            pods.append(
                workload_pod(
                    "oom-pod",
                    "2026-03-30T00:00:00Z",
                    {
                        "phase": "Running",
                        "containerStatuses": [{"name": "mem-eater", "lastState": {"terminated": {"reason": "OOMKilled"}}}],
                    },
                )
            )
        elif idx == 2:
            pods.append(
                {
                    "metadata": {
                        "name": "pending-pod",
                        "namespace": "default",
                        "creationTimestamp": "2026-03-29T22:00:00Z",
                    },
                    "status": {"phase": "Pending", "reason": "Unschedulable"},
                }
            )
        elif idx == 3:
            pods.append(
                workload_pod(
                    "evicted-pod",
                    "2026-03-29T20:00:00Z",
                    {"phase": "Failed", "reason": "Evicted"},
                )
            )
        elif idx == 4:
            pods.append(
                workload_pod(
                    "pull-error-pod",
                    "2026-03-30T01:00:00Z",
                    {
                        "phase": "Running",
                        "containerStatuses": [{"state": {"waiting": {"reason": "ImagePullBackOff"}}}],
                    },
                )
            )
        elif idx == 7:
            pods.append(
                workload_pod(
                    "prometheus-mcp-demo-pod",
                    "2026-03-30T00:00:00Z",
                    {"phase": "Running", "containerStatuses": [{"name": "app", "restartCount": 0, "ready": True}]},
                )
            )

        return pods

    def get_nodes(self) -> list[dict[str, Any]]:
        idx = get_current_anomaly_index()
        nodes = [{"metadata": {"name": "node-1"}, "status": {"conditions": [{"type": "Ready", "status": "True"}]}}]
        if idx == 5:
            nodes.append({"metadata": {"name": "node-2"}, "status": {"conditions": [{"type": "Ready", "status": "False"}]}})
        else:
            nodes.append({"metadata": {"name": "node-2"}, "status": {"conditions": [{"type": "Ready", "status": "True"}]}})
        return nodes

    def get_deployments_all_namespaces(self) -> list[dict[str, Any]]:
        idx = get_current_anomaly_index()
        deps = [
            {
                "metadata": {
                    "name": _MOCK_DEPLOYMENT,
                    "namespace": "default",
                    "creationTimestamp": "2026-03-30T00:00:00Z",
                },
                "spec": {"replicas": 3},
                "status": {
                    "updatedReplicas": 3,
                    "conditions": [{"type": "Progressing", "status": "True", "lastTransitionTime": "2026-03-30T00:00:00Z"}],
                },
            }
        ]
        if idx == 6:
            deps[0]["status"]["updatedReplicas"] = 1
            deps[0]["status"]["conditions"][0]["lastTransitionTime"] = "2020-01-01T00:00:00Z"
        return deps

    def describe_pod(self, namespace: str, name: str) -> str:
        return f"Mock describe pod {namespace}/{name}"

    def describe_deployment(self, namespace: str, name: str) -> str:
        return f"Name:\t{name}\nNamespace:\t{namespace}\nReplicas:\t3 desired | 3 updated | 3 available (mock)\n"

    def logs_pod(self, namespace: str, name: str, tail: int = 100) -> str:
        return (
            "FATAL Application startup failed: Unable to establish database connection\n"
            "java.lang.RuntimeException: Service unavailable"
        )

    def get_pod_json(self, namespace: str, name: str) -> dict[str, Any]:
        for p in self.get_pods_all_namespaces():
            m = p.get("metadata") or {}
            if m.get("name") == name and m.get("namespace", "default") == namespace:
                return p
        return {"metadata": {"name": name, "namespace": namespace, **_pod_owner_meta()}}

    def delete_pod(self, namespace: str, name: str) -> str:
        log.info("Mock cluster: deleted pod %s/%s", namespace, name)
        return f"Mock deleted pod {namespace}/{name}"

    def patch_deployment(self, namespace: str, name: str, patch: dict[str, Any]) -> str:
        log.info("Mock cluster: patched deployment %s/%s", namespace, name)
        return "Mock patch applied"

    def rollout_status_relaxed(self, namespace: str, deployment: str) -> tuple[int, str]:
        return 0, f"deployment {deployment!r} successfully rolled out (mock)"
