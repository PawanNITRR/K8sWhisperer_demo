from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from schemas.models import LogEntry
from agent.llm_factory import get_chat_model
from agent.prompts_util import load_prompt
from agent.state import AgentState
from config import get_settings
from mcp_servers.slack_mcp import SlackMCP
from utils.audit import AuditLogger
from utils.structured_logger import get_logger

log = get_logger(__name__)


def explain_node(state: AgentState) -> dict[str, Any]:
    settings = get_settings()
    primary = state.get("primary_anomaly")
    if not primary:
        summary = "No anomalies were detected in this observe cycle. No remediation was planned."
    elif state.get("approved") is False:
        summary = (
            "A human rejected the proposed remediation in the safety gate. "
            "No automatic kubectl changes were applied."
        )
    else:
        model = get_chat_model()
        sys = load_prompt("explain_system.txt")
        payload = {
            "anomaly": primary,
            "diagnosis": state.get("diagnosis"),
            "plan": state.get("plan"),
            "result": state.get("result"),
            "auto": state.get("should_auto_execute"),
        }
        msg = HumanMessage(content=json.dumps(payload, default=str)[:120_000])
        try:
            out = model.invoke([SystemMessage(content=sys), msg])
            summary = str(out.content).strip()
        except Exception as e:
            log.warning("explain LLM failed: %s", e)
            summary = f"Cycle completed. (Explain LLM error: {e})"

    audit = AuditLogger(settings.audit_log_path)
    entry = LogEntry(
        phase="explain",
        summary=summary,
        action_taken=(state.get("result") or None)[:20_000] if state.get("result") else None,
    )
    audit.append(entry)
    log.info("Audit: %s", summary[:160])

    if settings.slack_channel_id and settings.slack_bot_token:
        try:
            slack = SlackMCP()
            slack.post_plain_text(channel=settings.slack_channel_id, text=f"K8sWhisperer: {summary[:2800]}")
        except Exception as e:
            log.warning("Slack summary post failed: %s", e)

    return {}
