from __future__ import annotations

import requests
from typing import Any

from mcp_servers.base_mcp import BaseMCP
from config import get_settings


class PrometheusMCP(BaseMCP):
    def __init__(self):
        super().__init__("prometheus-mcp")
        settings = get_settings()
        # Example: http://localhost:9090 — leave unset in .env to disable Prometheus queries
        self.base_url = settings.prometheus_base_url
        self.mock = settings.mock_cluster

    def health(self) -> dict[str, Any]:
        if self.mock:
            return {"ok": True, "note": "Prometheus MCP in Mock Mode"}
        if not self.base_url:
            return {"ok": False, "error": "prometheus_base_url not configured"}

        try:
            res = requests.get(f"{self.base_url}/-/healthy", timeout=3)
            return {"ok": res.status_code == 200}
        except Exception as e:
            self.log.debug("Prometheus health check failed: %s", e)
            return {"ok": False, "error": str(e)}

    def query(self, promql: str) -> Any:
        if self.mock:
            from utils.mock_state import get_current_anomaly_index
            idx = get_current_anomaly_index()
            # CPU Throttling is anomaly 7 in the rotation
            if idx == 7:
                return {
                    "status": "success",
                    "data": {
                        "resultType": "vector",
                        "result": [
                            {
                                "metric": {"namespace": "default", "pod": "prometheus-mcp-demo-pod"},
                                "value": [1600000000.0, "0.85"],
                            }
                        ],
                    },
                }
            return {"status": "success", "data": {"resultType": "vector", "result": []}}

        if not self.base_url:
            raise RuntimeError("prometheus_base_url not configured")
        res = requests.get(
            f"{self.base_url}/api/v1/query",
            params={"query": promql},
            timeout=5,
        )
        res.raise_for_status()
        return res.json()



# ---------- SINGLETON ----------
_prometheus_client: PrometheusMCP | None = None


def get_prometheus_client() -> PrometheusMCP:
    global _prometheus_client
    if _prometheus_client is None:
        _prometheus_client = PrometheusMCP()
    return _prometheus_client