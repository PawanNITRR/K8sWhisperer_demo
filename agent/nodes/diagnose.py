from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from schemas.models import AffectedResource, DiagnosisOutcome
from agent.llm_factory import get_chat_model
from utils.llm_invoke import invoke_with_retry
from agent.prompts_util import load_prompt
from agent.state import AgentState
from config import get_settings
from mcp_servers.kubectl_mcp import get_kubectl_client
from schemas.constants import LOG_MAX_CHARS, LOG_TAIL_LINES
from utils.log_chunker import prepare_logs_for_llm
from utils.log_summarizer import summarize_logs_plain_english
from utils.structured_logger import get_logger

log = get_logger(__name__)


def diagnose_node(state: AgentState) -> dict[str, Any]:
    primary = state.get("primary_anomaly")
    if not primary:
        return {"diagnosis": "", "evidence_list": []}

    ar = AffectedResource.model_validate(primary["affected_resource"])
    k = get_kubectl_client()

    describe_txt = ""
    logs_txt = ""
    try:
        if ar.kind == "Pod":
            describe_txt = k.describe_pod(ar.namespace, ar.name)
            logs_txt = k.logs_pod(ar.namespace, ar.name, tail=300)
        elif ar.kind == "Deployment":
            describe_txt = k.describe_deployment(ar.namespace, ar.name)
        elif ar.kind == "Node":
            describe_txt = k.run(["describe", "node", ar.name])
    except Exception as e:
        describe_txt = f"(describe failed: {e})"

    settings = get_settings()
    if ar.kind == "Pod" and logs_txt:
        logs_txt = prepare_logs_for_llm(logs_txt, tail_line_count=LOG_TAIL_LINES, max_chars=LOG_MAX_CHARS)
        if settings.mock_cluster:
            logs_summary = "Mock pod log excerpt (LLM summarizer skipped when MOCK_CLUSTER=1)."
        else:
            logs_summary = summarize_logs_plain_english(logs_txt)
    else:
        logs_summary = "No pod logs available for analysis."

    if settings.mock_cluster:
        at = primary.get("type", "Unknown")
        sev = primary.get("severity", "")
        log.info("Diagnose: mock template for %s severity=%s", at, sev)
        return {
            "diagnosis": (
                f"Mock diagnosis — {at} (severity {sev}): matches the spec trigger; "
                "synthetic describe/logs below. In production, Gemini would expand this."
            ),
            "evidence_list": [describe_txt[:600], (logs_summary or "")[:600]],
        }

    model = get_chat_model()
    structured = model.with_structured_output(DiagnosisOutcome)
    sys = load_prompt("diagnose_system.txt")
    payload = {
        "anomaly": primary,
        "describe": describe_txt[:80_000],
        "logs": logs_summary,  # Use plain English summary instead of raw logs
    }
    msg = HumanMessage(content=json.dumps(payload, default=str))
    try:
        out = invoke_with_retry(
            lambda: structured.invoke([SystemMessage(content=sys), msg]),
            log=log,
            operation="diagnose",
        )
    except Exception as e:
        log.info("diagnose LLM unavailable: %s", e)
        out = DiagnosisOutcome(root_cause="Diagnosis unavailable (LLM error).", evidence_list=[str(e)])
    if out is None:
        out = DiagnosisOutcome(root_cause="Diagnosis unavailable (empty LLM response).", evidence_list=[])

    log.info("Diagnosis: %s", out.root_cause[:200])
    return {
        "diagnosis": out.root_cause,
        "evidence_list": out.evidence_list,
    }
