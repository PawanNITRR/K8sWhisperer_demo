from __future__ import annotations

import json
import time
from typing import Any

from schemas.constants import VERIFY_MAX_WAIT_SEC, VERIFY_POLL_BASE_SEC
from schemas.enums import ActionType
from schemas.models import RemediationPlan
from agent.state import AgentState
from mcp_servers.kubectl_mcp import KubectlMCP, get_kubectl_client
from mcp_servers.rbac_checker import RBACChecker
from utils.structured_logger import get_logger

log = get_logger(__name__)


def infer_deployment_name(k: KubectlMCP, namespace: str, pod_name: str) -> str | None:
    try:
        pod = k.get_pod_json(namespace, pod_name)
    except Exception:
        return None
    owners = pod.get("metadata", {}).get("ownerReferences") or []
    for o in owners:
        if o.get("kind") == "ReplicaSet":
            try:
                rs = json.loads(k.run(["get", "rs", "-n", namespace, o["name"], "-o", "json"]))
            except Exception:
                continue
            for o2 in rs.get("metadata", {}).get("ownerReferences") or []:
                if o2.get("kind") == "Deployment":
                    return o2.get("name")
    return None


def _verify_workload(
    k: KubectlMCP,
    plan: RemediationPlan,
    start: float,
    *,
    pod_deleted: bool,
) -> str:
    """Poll until deadline; prefer deployment rollout when available."""
    ns = plan.target.namespace
    name = plan.target.name
    dep = (plan.parameters or {}).get("deployment") if plan.parameters else None
    deadline = start + VERIFY_MAX_WAIT_SEC
    last = ""

    while time.time() < deadline:
        if dep:
            code, out = k.rollout_status_relaxed(ns, dep)
            if code == 0 and "successfully rolled out" in out.lower():
                return f"Verified deployment/{dep}: {out.strip()[:500]}"
            last = out
        if plan.target.kind == "Pod" and not pod_deleted:
            try:
                pod = k.get_pod_json(ns, name)
                phase = (pod.get("status") or {}).get("phase")
                if phase == "Running":
                    return f"Verified pod {ns}/{name} is Running."
            except RuntimeError as e:
                last = str(e)
            except Exception as e:
                last = str(e)
        time.sleep(VERIFY_POLL_BASE_SEC)

    return f"Verification timed out after {VERIFY_MAX_WAIT_SEC}s. Last note: {last}"


def _patch_resource_bump(k: KubectlMCP, namespace: str, deployment: str, pct: float, resource_type: str) -> str:
    out = k.run(["get", "deployment", "-n", namespace, deployment, "-o", "json"])
    dep = json.loads(out)
    containers = dep["spec"]["template"]["spec"]["containers"]
    patch_containers: list[dict[str, Any]] = []
    for c in containers:
        res = dict(c.get("resources") or {})
        limits = dict((res.get("limits") or {}))
        reqs = dict((res.get("requests") or {}))
        resource_lim = limits.get(resource_type)
        if resource_lim and isinstance(resource_lim, str):
            num, suf = _parse_quantity(resource_lim)
            if num is not None and suf:
                limits[resource_type] = f"{int(num * (1.0 + pct))}{suf}"
        resource_req = reqs.get(resource_type)
        if resource_req and isinstance(resource_req, str):
            num, suf = _parse_quantity(resource_req)
            if num is not None and suf:
                reqs[resource_type] = f"{int(num * (1.0 + pct))}{suf}"
        res["limits"] = limits
        res["requests"] = reqs
        nc = dict(c)
        nc["resources"] = res
        patch_containers.append(nc)
    patch = {"spec": {"template": {"spec": {"containers": patch_containers}}}}
    return k.patch_deployment(namespace, deployment, patch)


def _parse_quantity(s: str) -> tuple[int | None, str | None]:
    s = s.strip()
    for suf in ("Gi", "Mi", "G", "M"):
        if s.endswith(suf):
            try:
                return int(float(s[:-len(suf)])), suf
            except ValueError:
                return None, None
    return None, None


def execute_node(state: AgentState) -> dict[str, Any]:
    plan_raw = state.get("plan")
    if not plan_raw:
        return {"result": "No plan to execute."}

    plan = RemediationPlan.model_validate(plan_raw)
    rbac = RBACChecker()
    ok, msg = rbac.is_allowed(plan)
    if not ok:
        return {"result": f"Blocked by RBAC checker: {msg}"}

    k = get_kubectl_client()
    start = time.time()
    time.sleep(min(30, VERIFY_MAX_WAIT_SEC))

    try:
        if plan.action == ActionType.RESTART_POD or plan.action == ActionType.DELETE_POD:
            if plan.target.kind != "Pod":
                return {"result": "Target must be Pod for delete/restart."}
            dep = (plan.parameters or {}).get("deployment")
            if not dep:
                dep = infer_deployment_name(k, plan.target.namespace, plan.target.name)
            plan = plan.model_copy(update={"parameters": {**(plan.parameters or {}), "deployment": dep}})
            out = k.delete_pod(plan.target.namespace, plan.target.name)
            ver = _verify_workload(k, plan, start, pod_deleted=True)
            return {"result": f"kubectl delete pod output:\n{out}\n\n{ver}"}

        if plan.action == ActionType.PATCH_RESOURCE_LIMITS:
            dep_name = (plan.parameters or {}).get("deployment")
            if not dep_name and plan.target.kind == "Pod":
                dep_name = infer_deployment_name(k, plan.target.namespace, plan.target.name)
            if not dep_name:
                return {"result": "PATCH_RESOURCE_LIMITS requires deployment name in parameters or inferable owner."}

            # Handle memory bump
            mem_pct = float((plan.parameters or {}).get("bump_memory_pct", 0))
            cpu_pct = float((plan.parameters or {}).get("bump_cpu_pct", 0))

            if mem_pct > 0:
                patch_out = _patch_resource_bump(k, plan.target.namespace, dep_name, mem_pct, "memory")
                _ = k.run(["rollout", "restart", "-n", plan.target.namespace, f"deployment/{dep_name}"])
                plan2 = plan.model_copy(update={"parameters": {**(plan.parameters or {}), "deployment": dep_name}})
                ver = _verify_workload(k, plan2, start, pod_deleted=True)
                return {
                    "result": (
                        f"Patched deployment/{dep_name} memory (+{mem_pct:.0%}) and restarted rollout.\n{patch_out}\n\n{ver}"
                    )
                }
            elif cpu_pct > 0:
                patch_out = _patch_resource_bump(k, plan.target.namespace, dep_name, cpu_pct, "cpu")
                _ = k.run(["rollout", "restart", "-n", plan.target.namespace, f"deployment/{dep_name}"])
                plan2 = plan.model_copy(update={"parameters": {**(plan.parameters or {}), "deployment": dep_name}})
                ver = _verify_workload(k, plan2, start, pod_deleted=True)
                return {
                    "result": (
                        f"Patched deployment/{dep_name} CPU (+{cpu_pct:.0%}) and restarted rollout.\n{patch_out}\n\n{ver}"
                    )
                }
            else:
                return {"result": "PATCH_RESOURCE_LIMITS requires bump_memory_pct or bump_cpu_pct parameter."}

        if plan.action in (ActionType.NO_OP, ActionType.RECOMMEND_ONLY):
            return {"result": "No kubectl write performed (no_op/recommend_only)."}

        if plan.action == ActionType.ALERT_HUMAN:
            return {"result": "No kubectl write performed (alert_human)."}

        return {"result": f"Action {plan.action} not implemented in executor."}
    except Exception as e:
        log.exception("execute failed")
        return {"result": f"Execute failed: {e}"}
