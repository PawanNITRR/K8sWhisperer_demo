from __future__ import annotations

import re

from typing import Any


def deployment_rollout_in_progress(describe_text: str) -> bool:
    """
    Heuristic: kubectl describe deployment output during rollout.
    """
    t = describe_text.lower()
    if "waiting for deployment" in t:
        return True
    if "progressing" in t and "replicas" in t:
        # NewReplicaSet + old replicas scaling - weak signal
        if re.search(r"oldreplicasets:\s*<none>", t):
            return False
    if "progress deadline exceeded" in t:
        return False
    return "newreplicaset" in t and ("progressing" in t or "updating" in t)


def pod_has_rollout_in_progress(k: Any, namespace: str, pod_name: str) -> bool:
    """
    Resolve pod -> owner Deployment (best effort) and describe it.
    """
    try:
        pod = k.get_pod_json(namespace, pod_name)
    except Exception:
        return False
    owners = pod.get("metadata", {}).get("ownerReferences") or []
    for o in owners:
        if o.get("kind") == "ReplicaSet":
            rs_name = o.get("name")
            if not rs_name:
                continue
            try:
                out = k.run(["get", "replicaset", "-n", namespace, rs_name, "-o", "json"])
                import json

                rs = json.loads(out)
                inner = rs.get("metadata", {}).get("ownerReferences") or []
                for o2 in inner:
                    if o2.get("kind") == "Deployment":
                        dep_name = o2.get("name")
                        if dep_name:
                            desc = k.describe_deployment(namespace, dep_name)
                            return deployment_rollout_in_progress(desc)
            except Exception:
                continue
    return False
