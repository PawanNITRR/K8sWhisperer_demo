from schemas.enums import ActionType, AnomalyType

# Auto-execute only when confidence exceeds this and blast radius is low (see safety_gate).
SAFETY_CONFIDENCE_THRESHOLD = 0.8

# Observe loop interval (seconds).
POLL_INTERVAL_SEC = 30

# Verify after execute: initial wait then poll with backoff (executor also uses these).
VERIFY_INITIAL_SLEEP_SEC = 10
VERIFY_MAX_WAIT_SEC = 90
VERIFY_POLL_BASE_SEC = 10

# Log chunking defaults (diagnose).
LOG_TAIL_LINES = 100
LOG_MAX_CHARS = 48_000

# Actions that must never auto-execute regardless of confidence (RBAC + blast-radius guard).
DESTRUCTIVE_ACTIONS: frozenset[ActionType] = frozenset(
    {
        ActionType.DELETE_NAMESPACE,
        ActionType.NODE_DRAIN,
        ActionType.ROLLBACK_OR_FORCE_ROLLOUT,
        ActionType.ALERT_HUMAN,
    }
)

# Anomaly types that always require HITL before any write (never auto-fix).
HITL_ONLY_ANOMALIES: frozenset[AnomalyType] = frozenset(
    {
        AnomalyType.NODE_NOT_READY,
        AnomalyType.DEPLOYMENT_STALLED,
    }
)
