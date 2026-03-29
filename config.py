from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM: openai | anthropic | gemini | mock (no API calls; for CI/local smoke)
    llm_provider: str = Field(
        default="openai",
        description="openai | anthropic | gemini | mock",
    )
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    # Google AI / Gemini (same key as in Google AI Studio)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    # kubectl: optional full path to kubectl.exe (else looks for tools/kubectl.exe, then PATH "kubectl")
    kubectl_path: str | None = None
    # No real cluster: use in-memory fixtures (MOCK_CLUSTER=1) so main.py runs without kube-apiserver
    mock_cluster: bool = False
    # kubectl (PATH must include kubectl; kubeconfig standard locations)
    kubectl_timeout_sec: int = 120
    kubectl_context: str | None = None

    # Prometheus (optional)
    prometheus_base_url: str | None = None

    # Slack HITL
    slack_bot_token: str | None = None
    slack_signing_secret: str | None = None
    slack_channel_id: str | None = None

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8080

    # Audit
    audit_log_path: str = "audit_log.json"

    # State store (Slack dedupe + thread mapping)
    state_store_path: str = "data/state_store.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
