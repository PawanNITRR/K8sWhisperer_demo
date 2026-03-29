from __future__ import annotations

from schemas.models import RemediationPlan
from schemas.enums import ActionType, BlastRadius


class RBACChecker:
    """
    Simple safety layer.
    Blocks dangerous actions unless explicitly allowed.
    """

    def is_allowed(self, plan: RemediationPlan) -> tuple[bool, str]:
        # Block high blast radius
        if plan.blast_radius == BlastRadius.HIGH:
            return False, "High blast radius actions are blocked"

        # Allow safe actions
        if plan.action in (
            ActionType.RESTART_POD,
            ActionType.DELETE_POD,
            ActionType.NO_OP,
            ActionType.RECOMMEND_ONLY,
        ):
            return True, "Allowed"

        # Allow patch with caution
        if plan.action == ActionType.PATCH_RESOURCE_LIMITS:
            return True, "Allowed (resource patch)"

        # Alert is always safe
        if plan.action == ActionType.ALERT_HUMAN:
            return True, "Allowed (alert only)"

        return False, f"Action {plan.action} not allowed"