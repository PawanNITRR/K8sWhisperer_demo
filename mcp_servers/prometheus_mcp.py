from __future__ import annotations

from typing import Any

import httpx

from config import get_settings
from mcp_servers.base_mcp import BaseMCP


class PrometheusMCP(BaseMCP):
    name = "prometheus"

    def __init__(self) -> None:
        self._settings = get_settings()

    def health(self) -> dict:
        base = self._settings.prometheus_base_url
        if not base:
            return {"ok": False, "error": "prometheus_base_url not configured"}
        try:
            r = httpx.get(f"{base.rstrip('/')}/-/healthy", timeout=10.0)
            return {"ok": r.status_code < 400, "status": r.status_code}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def query(self, promql: str) -> dict[str, Any]:
        base = self._settings.prometheus_base_url
        if not base:
            return {"status": "skipped", "reason": "no prometheus_base_url"}
        url = f"{base.rstrip('/')}/api/v1/query"
        r = httpx.get(url, params={"query": promql}, timeout=15.0)
        r.raise_for_status()
        return r.json()
