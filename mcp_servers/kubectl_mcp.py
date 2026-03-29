from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from config import get_settings
from mcp_servers.base_mcp import BaseMCP
from mcp_servers.kubectl_mock import MockKubectlMCP
from utils.structured_logger import get_logger

log = get_logger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[1]


class KubectlMCP(BaseMCP):
    """
    In-process kubectl adapter (MCP-style tools). Uses subprocess kubectl with optional --context.
    """

    name = "kubectl"

    def __init__(self) -> None:
        self._settings = get_settings()

    def _kubectl_exe(self) -> str:
        s = self._settings
        if s.kubectl_path:
            return s.kubectl_path
        for name in ("kubectl.exe", "kubectl"):
            p = _REPO_ROOT / "tools" / name
            if p.is_file():
                return str(p)
        return "kubectl"

    def _base_cmd(self) -> list[str]:
        cmd = [self._kubectl_exe()]
        if self._settings.kubectl_context:
            cmd += ["--context", self._settings.kubectl_context]
        return cmd

    def run(self, args: list[str], *, input_text: str | None = None) -> str:
        cmd = self._base_cmd() + args
        log.debug("kubectl %s", " ".join(cmd))
        proc = subprocess.run(
            cmd,
            input=input_text.encode() if input_text else None,
            capture_output=True,
            timeout=self._settings.kubectl_timeout_sec,
        )
        if proc.returncode != 0:
            err = proc.stderr.decode(errors="replace") or proc.stdout.decode(errors="replace")
            raise RuntimeError(f"kubectl failed ({proc.returncode}): {err.strip()}")
        return proc.stdout.decode(errors="replace")

    def run_allow_fail(self, args: list[str]) -> tuple[int, str]:
        """Return (exit_code, stdout+stderr text) without raising on non-zero exit."""
        cmd = self._base_cmd() + args
        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=self._settings.kubectl_timeout_sec,
        )
        out = (proc.stdout.decode(errors="replace") + proc.stderr.decode(errors="replace")).strip()
        return proc.returncode, out

    def health(self) -> dict:
        try:
            v = self.run(["version", "-o", "json"])
            data = json.loads(v)
            return {"ok": True, "clientVersion": data.get("clientVersion"), "serverVersion": data.get("serverVersion")}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_events_all_namespaces(self) -> list[dict[str, Any]]:
        out = self.run(["get", "events", "-A", "-o", "json"])
        data = json.loads(out)
        return list(data.get("items") or [])

    def get_pods_all_namespaces(self) -> list[dict[str, Any]]:
        out = self.run(["get", "pods", "-A", "-o", "json"])
        data = json.loads(out)
        return list(data.get("items") or [])

    def get_nodes(self) -> list[dict[str, Any]]:
        out = self.run(["get", "nodes", "-o", "json"])
        data = json.loads(out)
        return list(data.get("items") or [])

    def get_deployments_all_namespaces(self) -> list[dict[str, Any]]:
        out = self.run(["get", "deployments", "-A", "-o", "json"])
        data = json.loads(out)
        return list(data.get("items") or [])

    def describe_pod(self, namespace: str, name: str) -> str:
        return self.run(["describe", "pod", "-n", namespace, name])

    def describe_deployment(self, namespace: str, name: str) -> str:
        return self.run(["describe", "deployment", "-n", namespace, name])

    def logs_pod(self, namespace: str, name: str, tail: int = 200) -> str:
        return self.run(["logs", "-n", namespace, name, f"--tail={tail}"])

    def rollout_status(self, namespace: str, deployment_name: str) -> str:
        return self.run(["rollout", "status", "-n", namespace, f"deployment/{deployment_name}"])

    def rollout_status_relaxed(self, namespace: str, deployment_name: str) -> tuple[int, str]:
        """Rollout status can be non-zero while a rollout is in progress."""
        return self.run_allow_fail(["rollout", "status", "-n", namespace, f"deployment/{deployment_name}"])

    def delete_pod(self, namespace: str, name: str) -> str:
        return self.run(["delete", "pod", "-n", namespace, name, "--ignore-not-found=true"])

    def patch_pod(self, namespace: str, name: str, patch: dict[str, Any]) -> str:
        payload = json.dumps(patch)
        return self.run(["patch", "pod", "-n", namespace, name, "-p", payload, "--type=merge"])

    def patch_deployment(self, namespace: str, name: str, patch: dict[str, Any]) -> str:
        payload = json.dumps(patch)
        return self.run(["patch", "deployment", "-n", namespace, name, "-p", payload, "--type=merge"])

    def get_pod_json(self, namespace: str, name: str) -> dict[str, Any]:
        out = self.run(["get", "pod", "-n", namespace, name, "-o", "json"])
        return json.loads(out)


def get_kubectl_client() -> KubectlMCP | MockKubectlMCP:
    """Return real kubectl adapter or mock cluster (see Settings.mock_cluster)."""
    if get_settings().mock_cluster:
        return MockKubectlMCP()
    return KubectlMCP()
