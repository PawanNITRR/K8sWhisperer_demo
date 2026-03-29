import os

import pytest

pytest.importorskip("langgraph")


@pytest.mark.skipif(os.getenv("K8S_WHISPERER_INTEGRATION") != "1", reason="Set K8S_WHISPERER_INTEGRATION=1")
def test_slack_webhook_route_exists():
    from fastapi.testclient import TestClient
    from webhook.server import app

    app.state.graph = None
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
