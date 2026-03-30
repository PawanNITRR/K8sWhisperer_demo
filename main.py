from __future__ import annotations

import threading
import time
import uuid

import uvicorn

from agent.graph import build_graph
from config import get_settings
from schemas.constants import POLL_INTERVAL_SEC
from utils.mock_state import advance_anomaly, get_mock_scenario_label
from utils.structured_logger import get_logger
from webhook.server import app as api_app

log = get_logger(__name__)


def run_api(host: str, port: int) -> None:
    uvicorn.run(api_app, host=host, port=port, log_level="info")


def main() -> None:
    settings = get_settings()
    graph = build_graph()
    api_app.state.graph = graph

    api_thread = threading.Thread(
        target=run_api,
        kwargs={"host": settings.api_host, "port": settings.api_port},
        daemon=True,
    )
    api_thread.start()
    log.info(
        "K8sWhisperer started: poll=%ss api=http://%s:%s health=/health slack=/slack/interactions",
        POLL_INTERVAL_SEC,
        settings.api_host,
        settings.api_port,
    )

    while True:
        thread_id = str(uuid.uuid4())
        if settings.mock_cluster:
            log.info("Mock scenario (this cycle): %s", get_mock_scenario_label())
        try:
            graph.invoke({}, config={"configurable": {"thread_id": thread_id}})
        except Exception:
            log.exception("Graph cycle failed")
        else:
            if settings.mock_cluster:
                advance_anomaly()
                log.info(
                    "Mock: next scenario in %ss -> %s",
                    POLL_INTERVAL_SEC,
                    get_mock_scenario_label(),
                )
        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
