from __future__ import annotations

from schemas.enums import ActionType
from schemas.models import RemediationPlan


class RBACChecker:
    """
    Validates remediation actions against an allowlist before any kubectl write.
    Narrow scope: prefer pod-level operations; block cluster-wide destructive ops.
    """

    ALLOWED_ACTIONS: frozenset[ActionType] = frozenset(
        {
            ActionType.RESTART_POD,
            ActionType.DELETE_POD,
            ActionType.PATCH_RESOURCE_LIMITS,
            ActionType.RECOMMEND_ONLY,
            ActionType.ALERT_HUMAN,
            ActionType.NO_OP,
        }
    )

    def is_allowed(self, plan: RemediationPlan) -> tuple[bool, str]:
        if plan.action not in self.ALLOWED_ACTIONS:
            return False, f"Action {plan.action} is not in the RBAC allowlist."
        if plan.target.kind not in {"Pod", "Deployment"}:
            return False, f"Target kind {plan.target.kind} is not permitted for automated writes."
        return True, "ok"
