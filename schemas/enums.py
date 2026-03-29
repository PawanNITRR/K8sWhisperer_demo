from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BlastRadius(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AnomalyType(str, Enum):
    CRASH_LOOP_BACK_OFF = "CrashLoopBackOff"
    OOM_KILLED = "OOMKilled"
    PENDING_POD = "PendingPod"
    IMAGE_PULL_BACK_OFF = "ImagePullBackOff"
    CPU_THROTTLING = "CPUThrottling"
    EVICTED_POD = "EvictedPod"
    DEPLOYMENT_STALLED = "DeploymentStalled"
    NODE_NOT_READY = "NodeNotReady"
    UNKNOWN = "Unknown"


class ActionType(str, Enum):
    RESTART_POD = "restart_pod"
    PATCH_RESOURCE_LIMITS = "patch_resource_limits"
    DELETE_POD = "delete_pod"
    RECOMMEND_ONLY = "recommend_only"
    ALERT_HUMAN = "alert_human"
    ROLLBACK_OR_FORCE_ROLLOUT = "rollback_or_force_rollout"
    NODE_DRAIN = "node_drain"
    DELETE_NAMESPACE = "delete_namespace"
    NO_OP = "no_op"
    OTHER = "other"
