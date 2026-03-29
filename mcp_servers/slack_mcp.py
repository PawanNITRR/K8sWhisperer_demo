from __future__ import annotations

from typing import Any

import requests

from mcp_servers.base_mcp import BaseMCP
from config import get_settings


class SlackMCP(BaseMCP):
    def __init__(self):
        super().__init__("slack-mcp")
        settings = get_settings()
        self.token = settings.slack_bot_token

    def health(self) -> dict[str, Any]:
        """Check if Slack token is configured."""
        if not self.token:
            return {"ok": False, "error": "Slack token not configured"}
        return {"ok": True}

    def post_plain_text(self, channel: str, text: str) -> None:
        if not self.token:
            self.log.warning("Slack token not configured")
            return

        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "channel": channel,
            "text": text,
        }

        res = requests.post(url, json=payload, headers=headers)
        if not res.ok or not res.json().get("ok"):
            raise RuntimeError(f"Slack API error: {res.text}")


# ---------- SINGLETON ----------
_slack_client: SlackMCP | None = None


def get_slack_client():
    global _slack_client
    if _slack_client is None:
        _slack_client = SlackMCP()
    return _slack_client