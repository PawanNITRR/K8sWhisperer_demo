import os

import pytest

pytest.importorskip("langgraph")


@pytest.mark.skipif(os.getenv("K8S_WHISPERER_INTEGRATION") != "1", reason="Set K8S_WHISPERER_INTEGRATION=1")
def test_rule_detector_oom_string():
    from agent.rule_detector import detect_from_pod_items

    pod = {
        "metadata": {"namespace": "default", "name": "p1"},
        "status": {
            "phase": "Running",
            "containerStatuses": [
                {
                    "name": "c1",
                    "restartCount": 1,
                    "lastState": {"terminated": {"reason": "OOMKilled"}},
                }
            ],
        },
    }
    anoms = detect_from_pod_items([pod])
    assert len(anoms) >= 1
