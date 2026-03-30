from __future__ import annotations

from schemas.models import RemediationPlan
from schemas.enums import ActionType, BlastRadius


class RBACChecker:
    """
    Simple safety layer.
    Blocks dangerous actions unless explicitly allowed.
    """

    def is_allowed(self, plan: RemediationPlan) -> tuple[bool, str]:
        # No cluster writes — always allow through executor (executor is a no-op for these)
        if plan.action in (
            ActionType.ALERT_HUMAN,
            ActionType.NO_OP,
            ActionType.RECOMMEND_ONLY,
        ):
            return True, "Allowed (no cluster write)"

        if plan.blast_radius == BlastRadius.HIGH:
            return False, "High blast radius actions are blocked"

        if plan.action in (
            ActionType.RESTART_POD,
            ActionType.DELETE_POD,
        ):
            return True, "Allowed"

        if plan.action == ActionType.PATCH_RESOURCE_LIMITS:
            return True, "Allowed (resource patch)"

        return False, f"Action {plan.action} not allowed"


# ---------- SINGLETON ----------
_rbac_checker: RBACChecker | None = None


def get_rbac_checker() -> RBACChecker:
    global _rbac_checker
    if _rbac_checker is None:
        _rbac_checker = RBACChecker()
    return _rbac_checker