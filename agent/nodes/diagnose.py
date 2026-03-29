from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from schemas.models import AffectedResource, DiagnosisOutcome
from agent.llm_factory import get_chat_model
from agent.prompts_util import load_prompt
from agent.state import AgentState
from mcp_servers.kubectl_mcp import get_kubectl_client
from schemas.constants import LOG_MAX_CHARS, LOG_TAIL_LINES
from utils.log_chunker import prepare_logs_for_llm
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

    if ar.kind == "Pod" and logs_txt:
        logs_txt = prepare_logs_for_llm(logs_txt, tail_line_count=LOG_TAIL_LINES, max_chars=LOG_MAX_CHARS)

    model = get_chat_model()
    structured = model.with_structured_output(DiagnosisOutcome)
    sys = load_prompt("diagnose_system.txt")
    payload = {
        "anomaly": primary,
        "describe": describe_txt[:80_000],
        "logs": logs_txt[:80_000],
    }
    msg = HumanMessage(content=json.dumps(payload, default=str))
    try:
        out: DiagnosisOutcome | None = structured.invoke([SystemMessage(content=sys), msg])
    except Exception as e:
        log.warning("diagnose LLM failed: %s", e)
        out = DiagnosisOutcome(root_cause="Diagnosis unavailable (LLM error).", evidence_list=[str(e)])
    if out is None:
        out = DiagnosisOutcome(root_cause="Diagnosis unavailable (empty LLM response).", evidence_list=[])

    log.info("Diagnosis: %s", out.root_cause[:200])
    return {
        "diagnosis": out.root_cause,
        "evidence_list": out.evidence_list,
    }
