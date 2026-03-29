from schemas.enums import AnomalyType, Severity
from schemas.models import AffectedResource, Anomaly, ClusterSnapshot


def test_anomaly_roundtrip():
    a = Anomaly(
        type=AnomalyType.CRASH_LOOP_BACK_OFF,
        severity=Severity.HIGH,
        affected_resource=AffectedResource(namespace="ns", name="p1"),
        confidence=0.9,
    )
    d = a.model_dump(mode="json")
    a2 = Anomaly.model_validate(d)
    assert a2.type == AnomalyType.CRASH_LOOP_BACK_OFF


def test_cluster_snapshot_defaults():
    s = ClusterSnapshot()
    assert s.events == []
    assert s.pods_summary == []
