from __future__ import annotations

from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config import get_settings
from mcp_servers.base_mcp import BaseMCP
from utils.structured_logger import get_logger

log = get_logger(__name__)


class SlackMCP(BaseMCP):
    """Post Block Kit messages for HITL approval."""

    name = "slack"

    def __init__(self) -> None:
        self._settings = get_settings()
        token = self._settings.slack_bot_token
        self._client = WebClient(token=token) if token else None

    def health(self) -> dict:
        if not self._client:
            return {"ok": False, "error": "slack_bot_token not set"}
        try:
            auth = self._client.auth_test()
            return {"ok": True, "team": auth.get("team"), "user": auth.get("user")}
        except SlackApiError as e:
            return {"ok": False, "error": str(e)}

    def post_plain_text(self, *, channel: str, text: str) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Slack client not configured")
        resp = self._client.chat_postMessage(channel=channel, text=text[:3900])
        return {"ok": resp.get("ok"), "ts": resp.get("ts")}

    def post_hitl_message(
        self,
        *,
        channel: str,
        thread_ts: str | None,
        title: str,
        blocks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Slack client not configured")
        kwargs: dict[str, Any] = {"channel": channel, "text": title, "blocks": blocks}
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
        resp = self._client.chat_postMessage(**kwargs)
        return {"ok": resp.get("ok"), "ts": resp.get("ts"), "channel": resp.get("channel")}
