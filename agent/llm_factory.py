from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable
import json

from config import get_settings


class MockChatModel(BaseChatModel):
    """Deterministic stub for tests and local smoke without API keys."""

    def _generate(self, messages: list[BaseMessage], stop: list[str] | None = None, **kwargs: Any) -> ChatResult:
        text = self._mock_reply(messages)
        gen = ChatGeneration(message=AIMessage(content=text))
        return ChatResult(generations=[gen])

    @property
    def _llm_type(self) -> str:
        return "mock-chat"

    def _mock_reply(self, messages: list[BaseMessage]) -> str:
        full = " ".join(str(m.content) for m in messages).lower()
        
        # Priority 1: Alerting
        if "alert decision" in full or "should a human be alerted" in full or "devops alert" in full:
            return '{"should_alert": true, "reason": "Mock: high severity anomaly requires human notification."}'
        
        # Priority 2: Diagnosis (Check this before detection because diagnosis payload contains the word 'anomaly')
        if "diagnos" in full or "root cause" in full or "sre" in full:
            return '{"root_cause": "Mock diagnosis: Component failed to initialize due to resource constraints.", "evidence_list": ["Log pattern match", "Metric threshold exceeded"]}'
            
        # Priority 3: Remediation / Plan
        if "remediation" in full or "plan" in full or "action" in full:
            return (
                '{"action": "restart_pod", '
                '"target": {"kind": "Pod", "namespace": "default", "name": "mock-pod"}, '
                '"parameters": {}, "confidence": 0.85, "blast_radius": "low", '
                '"rationale": "Restarting is the standard first step for this anomaly."}'
            )

        # Priority 4: Detection / Classification
        if "anomalies" in full or "classify" in full or "detect" in full or "anomaly" in full:
            from utils.mock_state import get_current_anomaly_index
            idx = get_current_anomaly_index()
            # We return different anomalies based on the current rotation index
            anomaly_types = ["CrashLoopBackOff", "OOMKilled", "PendingPod", "EvictedPod", "ImagePullBackOff", "NodeNotReady", "DeploymentStalled", "CPUThrottling"]
            t = anomaly_types[idx % len(anomaly_types)]
            return (
                f'{{"anomalies": [{{"type": "{t}", "severity": "high", '
                f'"affected_resource": {{"kind": "Pod", "namespace": "default", "name": "mock-pod-{idx}"}}, '
                f'"confidence": 0.9, "trigger_signal": "mock", "notes": "Automated mock detection"}}]}}'
            )
            
        # Priority 5: Explanation / Summary
        if "summary" in full or "audit" in full or "explain" in full:
            return "The agent observed the cluster, detected an anomaly, and prepared a remediation plan."
            
        return '{"ok": true}'

    def bind_tools(self, tools: Any, **kwargs: Any) -> BaseChatModel:
        return self

    def with_structured_output(self, schema: Any, **kwargs: Any) -> Runnable:
        return MockStructuredRunnable(schema, self._mock_reply)


class MockStructuredRunnable(Runnable):
    def __init__(self, schema: Any, mock_fn: Any):
        self.schema = schema
        self.mock_fn = mock_fn

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        text = self.mock_fn(input)
        try:
            data = json.loads(text)
            if hasattr(self.schema, "model_validate"):
                result = self.schema.model_validate(data)
                return result
            return data
        except Exception:
            # If validation fails, return a dummy instance of the schema to prevent crashes
            if hasattr(self.schema, "model_validate"):
                # Return an empty/default instance if schema is a Pydantic model
                try:
                    return self.schema.model_construct(**json.loads(text))
                except:
                    # Last resort: just return an empty instance if possible
                    try: return self.schema()
                    except: return data
            return json.loads(text)


def get_chat_model() -> BaseChatModel:
    s = get_settings()
    provider = s.llm_provider.lower()
    if provider == "mock":
        return MockChatModel()
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if not s.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY required when llm_provider=anthropic")
        return ChatAnthropic(
            model=s.anthropic_model,
            api_key=s.anthropic_api_key,
            temperature=0,
            max_retries=8,
        )
    if provider in ("gemini", "google"):
        from langchain_google_genai import ChatGoogleGenerativeAI

        key = s.gemini_api_key
        if not key:
            raise ValueError("GEMINI_API_KEY required when llm_provider=gemini (or google)")
        return ChatGoogleGenerativeAI(
            model=s.gemini_model,
            google_api_key=key,
            temperature=0,
            max_retries=8,
        )
    from langchain_openai import ChatOpenAI

    if not s.openai_api_key:
        raise ValueError("OPENAI_API_KEY required when llm_provider=openai")
    return ChatOpenAI(
        model=s.openai_model,
        api_key=s.openai_api_key,
        temperature=0,
        max_retries=8,
    )
