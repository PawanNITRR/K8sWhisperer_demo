from schemas.enums import ActionType, AnomalyType, BlastRadius
from schemas.models import AffectedResource, RemediationPlan
from agent.nodes.safety_gate import should_auto_execute


def test_auto_execute_allowed_for_safe_restart():
    plan = RemediationPlan(
        action=ActionType.RESTART_POD,
        target=AffectedResource(namespace="ns", name="pod-a"),
        confidence=0.9,
        blast_radius=BlastRadius.LOW,
    )
    assert should_auto_execute(plan, AnomalyType.CRASH_LOOP_BACK_OFF) is True


def test_node_not_ready_always_hitl():
    plan = RemediationPlan(
        action=ActionType.RECOMMEND_ONLY,
        target=AffectedResource(kind="Node", namespace="", name="node-1"),
        confidence=0.99,
        blast_radius=BlastRadius.LOW,
    )
    assert should_auto_execute(plan, AnomalyType.NODE_NOT_READY) is False


def test_destructive_action_blocked():
    plan = RemediationPlan(
        action=ActionType.ALERT_HUMAN,
        target=AffectedResource(namespace="ns", name="x"),
        confidence=0.99,
        blast_radius=BlastRadius.LOW,
    )
    assert should_auto_execute(plan, AnomalyType.IMAGE_PULL_BACK_OFF) is False


def test_low_confidence_blocked():
    plan = RemediationPlan(
        action=ActionType.RESTART_POD,
        target=AffectedResource(namespace="ns", name="pod-a"),
        confidence=0.5,
        blast_radius=BlastRadius.LOW,
    )
    assert should_auto_execute(plan, AnomalyType.CRASH_LOOP_BACK_OFF) is False


def test_high_blast_radius_blocked():
    plan = RemediationPlan(
        action=ActionType.RESTART_POD,
        target=AffectedResource(namespace="ns", name="pod-a"),
        confidence=0.99,
        blast_radius=BlastRadius.HIGH,
    )
    assert should_auto_execute(plan, AnomalyType.CRASH_LOOP_BACK_OFF) is False
