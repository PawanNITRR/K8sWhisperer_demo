from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm_factory import get_chat_model
from agent.prompts_util import load_prompt
from agent.state import AgentState
from config import get_settings
from mcp_servers.slack_mcp import get_slack_client
from schemas.models import LogEntry
from utils.audit import AuditLogger
from utils.llm_invoke import invoke_with_retry
from utils.structured_logger import get_logger

log = get_logger(__name__)


def _resource_ref_from_state(primary: dict[str, Any] | None, plan: dict[str, Any] | None) -> str:
    if isinstance(primary, dict):
        ar = primary.get("affected_resource")
        if isinstance(ar, dict) and ar.get("name"):
            return f"{ar.get('kind', 'Pod')}/{ar.get('namespace', 'default')}/{ar['name']}"
    if isinstance(plan, dict):
        t = plan.get("target")
        if isinstance(t, dict) and t.get("name"):
            return f"{t.get('kind', 'Pod')}/{t.get('namespace', 'default')}/{t['name']}"
    return "cluster"


def _anomaly_type_str(primary: dict[str, Any] | None) -> str | None:
    if isinstance(primary, dict) and primary.get("type") is not None:
        return str(primary["type"])
    return None


def _planned_action_str(plan: dict[str, Any] | None) -> str | None:
    if isinstance(plan, dict) and plan.get("action") is not None:
        return str(plan["action"])
    return None


def _action_display_label(
    planned: str | None,
    resource_ref: str,
    result: str | None,
) -> str | None:
    if planned and resource_ref != "cluster":
        return f"{planned} @ {resource_ref}"
    if planned:
        return planned
    if result:
        return "executed (see execution_detail)"
    return None


def explain_node(state: AgentState) -> dict[str, Any]:
    settings = get_settings()
    primary = state.get("primary_anomaly")
    primary_d = primary if isinstance(primary, dict) else None
    plan_d = state.get("plan") if isinstance(state.get("plan"), dict) else None
    resource_ref = _resource_ref_from_state(primary_d, plan_d)
    anomaly_type = _anomaly_type_str(primary_d)
    planned_action = _planned_action_str(plan_d)
    hitl_involved = state.get("approved") is not None
    if not primary:
        summary = "No anomalies were detected in this observe cycle. No remediation was planned."
    elif state.get("approved") is False:
        summary = (
            "A human rejected the proposed remediation in the safety gate. "
            "No automatic kubectl changes were applied."
        )
    elif settings.mock_cluster and primary:
        plan = state.get("plan") or {}
        act = plan.get("action", "none") if isinstance(plan, dict) else "none"
        summary = (
            f"[MOCK_CLUSTER] Anomaly {primary.get('type')} (sev={primary.get('severity')}). "
            f"Diagnosis: {(state.get('diagnosis') or '')[:220]}… "
            f"Planned action: {act}. "
            f"Execution: {(state.get('result') or 'n/a')[:280]}"
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
            out = invoke_with_retry(
                lambda: model.invoke([SystemMessage(content=sys), msg]),
                log=log,
                operation="explain",
            )
            summary = str(out.content).strip()
        except Exception as e:
            log.info("explain LLM unavailable: %s", e)
            summary = f"Cycle completed. (Explain LLM error: {e})"

    audit = AuditLogger(settings.audit_log_path)
    result_raw = state.get("result")
    action_label = _action_display_label(planned_action, resource_ref, result_raw if isinstance(result_raw, str) else None)
    entry = LogEntry(
        phase="explain",
        summary=summary,
        action_taken=action_label,
        anomaly_type=anomaly_type,
        resource_ref=resource_ref,
        planned_action=planned_action,
        execution_detail=(result_raw[:20_000] if isinstance(result_raw, str) else None),
        hitl_involved=hitl_involved,
    )
    audit.append(entry)
    log.info("Audit: %s", summary[:160])

    # HITL already sent Approve/Reject Block Kit from hitl_node — do not spam a second plain-text-only message.
    if settings.slack_channel_id and settings.slack_bot_token and state.get("should_alert", False):
        if hitl_involved:
            log.info("Slack: skipping explain plain-text post (HITL approve/reject message was already sent).")
        else:
            try:
                slack = get_slack_client()
                slack.post_plain_text(
                    channel=settings.slack_channel_id,
                    text=f"K8sWhisperer alert: {anomaly_type or 'issue'} @ {resource_ref}\n{summary[:2800]}",
                )
            except Exception as e:
                log.info("Slack summary post skipped: %s", e)

    return {}
