from __future__ import annotations

import json
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from agent.state import AgentState
from config import get_settings
from mcp_servers.slack_mcp import get_slack_client
from utils.structured_logger import get_logger

log = get_logger(__name__)


def _slack_blocks(thread_id: str, plan: dict, diagnosis: str) -> list[dict[str, Any]]:
    return [
        {"type": "header", "text": {"type": "plain_text", "text": "K8sWhisperer approval required"}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Diagnosis*\n{diagnosis[:2800]}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Plan*\n```{json.dumps(plan, indent=2, default=str)[:2800]}```",
            },
        },
        {
            "type": "actions",
            "block_id": "hitl_actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "style": "primary",
                    "value": thread_id,
                    "action_id": "k8sw_hitl_approve",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject"},
                    "style": "danger",
                    "value": thread_id,
                    "action_id": "k8sw_hitl_reject",
                },
            ],
        },
    ]


def hitl_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Human-in-the-loop: Slack message (if configured) then LangGraph interrupt until webhook resumes.
    """
    settings = get_settings()
    thread_id = str(config.get("configurable", {}).get("thread_id", "default"))
    plan = state.get("plan") or {}
    diagnosis = state.get("diagnosis") or ""

    slack = get_slack_client()
    if settings.slack_channel_id and settings.slack_bot_token:
        try:
            slack.post_hitl_message(
                channel=settings.slack_channel_id,
                thread_ts=None,
                title="K8sWhisperer HITL",
                blocks=_slack_blocks(thread_id, plan, diagnosis),
            )
        except Exception as e:
            log.warning("Slack post failed (continuing to interrupt): %s", e)

    resume = interrupt(
        {
            "kind": "hitl",
            "thread_id": thread_id,
            "cycle_id": state.get("cycle_id"),
            "plan": plan,
        }
    )
    if isinstance(resume, dict):
        approved = bool(resume.get("approved"))
    else:
        approved = bool(resume)
    log.info("HITL resume: approved=%s", approved)
    return {"approved": approved}
