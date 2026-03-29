from __future__ import annotations

import requests
from typing import Any

from mcp_servers.base_mcp import BaseMCP
from config import get_settings


class PrometheusMCP(BaseMCP):
    def __init__(self):
        super().__init__("prometheus-mcp")
        settings = get_settings()
        # Example: http://localhost:9090
        self.base_url = getattr(settings, "prometheus_url", "http://localhost:9090")

    def health(self) -> dict[str, Any]:
        try:
            res = requests.get(f"{self.base_url}/-/healthy", timeout=3)
            return {"ok": res.status_code == 200}
        except Exception as e:
            self.log.warning("Prometheus health check failed: %s", e)
            return {"ok": False, "error": str(e)}

    def query(self, promql: str) -> Any:
        res = requests.get(
            f"{self.base_url}/api/v1/query",
            params={"query": promql},
            timeout=5,
        )
        res.raise_for_status()
        return res.json()