from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

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
        last = str(messages[-1].content) if messages else ""
        if "anomalies" in last.lower() or "classify" in last.lower():
            return (
                '{"anomalies": [{"type": "CrashLoopBackOff", "severity": "high", '
                '"affected_resource": {"kind": "Pod", "namespace": "default", "name": "demo"}, '
                '"confidence": 0.9, "trigger_signal": "mock", "notes": "mock"}]}'
            )
        if "diagnos" in last.lower():
            return '{"root_cause": "Mock diagnosis: container exits immediately.", "evidence_list": ["mock evidence"]}'
        if "remediation" in last.lower() or "plan" in last.lower():
            return (
                '{"action": "restart_pod", '
                '"target": {"kind": "Pod", "namespace": "default", "name": "demo"}, '
                '"parameters": {}, "confidence": 0.85, "blast_radius": "low", '
                '"rationale": "Restart pod to recover from crash loop."}'
            )
        if "summary" in last.lower() or "audit" in last.lower():
            return "Mock summary: observed cluster, evaluated anomalies, and recorded audit entry."
        return '{"ok": true}'

    def bind_tools(self, tools: Any, **kwargs: Any) -> BaseChatModel:
        return self


def get_chat_model() -> BaseChatModel:
    s = get_settings()
    provider = s.llm_provider.lower()
    if provider == "mock":
        return MockChatModel()
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if not s.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY required when llm_provider=anthropic")
        return ChatAnthropic(model=s.anthropic_model, api_key=s.anthropic_api_key, temperature=0)
    if provider in ("gemini", "google"):
        from langchain_google_genai import ChatGoogleGenerativeAI

        key = s.gemini_api_key
        if not key:
            raise ValueError("GEMINI_API_KEY required when llm_provider=gemini (or google)")
        return ChatGoogleGenerativeAI(
            model=s.gemini_model,
            google_api_key=key,
            temperature=0,
        )
    from langchain_openai import ChatOpenAI

    if not s.openai_api_key:
        raise ValueError("OPENAI_API_KEY required when llm_provider=openai")
    return ChatOpenAI(model=s.openai_model, api_key=s.openai_api_key, temperature=0)
