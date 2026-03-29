import os

import pytest

pytest.importorskip("langgraph")


@pytest.mark.skipif(os.getenv("K8S_WHISPERER_INTEGRATION") != "1", reason="Set K8S_WHISPERER_INTEGRATION=1 and configure kubeconfig")
def test_kubectl_reachable():
    from mcp_servers.kubectl_mcp import KubectlMCP

    k = KubectlMCP()
    h = k.health()
    assert h.get("ok") is True
