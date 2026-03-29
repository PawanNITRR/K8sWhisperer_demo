import pytest

pytest.importorskip("langgraph")


def test_pick_primary_orders_by_severity():
    from schemas.enums import AnomalyType, Severity
    from schemas.models import AffectedResource, Anomaly
    from agent.nodes.detect import pick_primary

    a = Anomaly(
        type=AnomalyType.PENDING_POD,
        severity=Severity.MEDIUM,
        affected_resource=AffectedResource(namespace="ns", name="a"),
        confidence=0.9,
    )
    b = Anomaly(
        type=AnomalyType.CRASH_LOOP_BACK_OFF,
        severity=Severity.HIGH,
        affected_resource=AffectedResource(namespace="ns", name="b"),
        confidence=0.5,
    )
    p = pick_primary([a, b])
    assert p is not None
    assert p.type == AnomalyType.CRASH_LOOP_BACK_OFF
