from __future__ import annotations

import json
import urllib.parse
from typing import Any

from fastapi import HTTPException, Request
from langgraph.types import Command

from config import get_settings
from utils.structured_logger import get_logger
from webhook.state_store import StateStore
from webhook.verification import verify_slack_request

log = get_logger(__name__)


async def slack_interactions(request: Request) -> dict[str, Any]:
    """
    Slack interactivity endpoint: resumes LangGraph after HITL interrupt.
    Expects application/x-www-form-urlencoded with `payload` JSON.
    """
    settings = get_settings()
    raw = await request.body()
    ts = request.headers.get("X-Slack-Request-Timestamp", "")
    sig = request.headers.get("X-Slack-Signature", "")
    if settings.slack_signing_secret:
        if not verify_slack_request(settings.slack_signing_secret, raw, ts, sig):
            raise HTTPException(status_code=401, detail="invalid slack signature")

    qs = urllib.parse.parse_qs(raw.decode("utf-8"))
    payload_raw = (qs.get("payload") or [None])[0]
    if not payload_raw:
        raise HTTPException(status_code=400, detail="missing payload")
    payload = json.loads(str(payload_raw))

    action = (payload.get("actions") or [{}])[0]
    action_id = action.get("action_id") or ""
    thread_id = action.get("value") or ""
    user_id = (payload.get("user") or {}).get("id") or ""
    msg_ts = payload.get("message_ts") or ""
    action_ts = action.get("action_ts") or ""
    callback_id = f"{msg_ts}:{user_id}:{action_id}:{action_ts}"

    store = StateStore()
    if store.seen_action(callback_id):
        log.info("Duplicate Slack interaction ignored: %s", callback_id)
        return {"ok": True}

    approved = action_id == "k8sw_hitl_approve"
    store.mark_action(callback_id)

    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        log.error("Graph not mounted on app.state")
        raise HTTPException(status_code=500, detail="graph not initialized")

    if not thread_id:
        raise HTTPException(status_code=400, detail="missing thread id")

    graph.invoke(Command(resume={"approved": approved}), config={"configurable": {"thread_id": thread_id}})
    return {"ok": True}
