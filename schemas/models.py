from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from schemas.enums import ActionType, AnomalyType, BlastRadius, Severity


class AffectedResource(BaseModel):
    """Kubernetes object the anomaly refers to."""

    kind: str = "Pod"
    namespace: str = "default"
    name: str
    api_version: str = "v1"


class Anomaly(BaseModel):
    type: AnomalyType
    severity: Severity
    affected_resource: AffectedResource
    confidence: float = Field(ge=0.0, le=1.0)
    trigger_signal: str | None = None
    notes: str | None = None


class DiagnosisOutcome(BaseModel):
    root_cause: str
    evidence_list: list[str] = Field(default_factory=list)


class RemediationPlan(BaseModel):
    action: ActionType
    target: AffectedResource
    parameters: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    blast_radius: BlastRadius
    rationale: str | None = None


class LogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    phase: str
    summary: str
    action_taken: str | None = None


class AlertDecision(BaseModel):
    should_alert: bool
    reason: str


class ClusterSnapshot(BaseModel):
    """Structured view built in Observe (normalized cluster state)."""

    events: list[dict[str, Any]] = Field(default_factory=list)
    pods_summary: list[dict[str, Any]] = Field(default_factory=list)
    nodes_summary: list[dict[str, Any]] = Field(default_factory=list)
    deployments_summary: list[dict[str, Any]] = Field(default_factory=list)
    prometheus_snippets: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)
