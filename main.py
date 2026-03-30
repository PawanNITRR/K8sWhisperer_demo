from __future__ import annotations

import threading
import time
import uuid

import uvicorn

from config import get_settings
from schemas.constants import POLL_INTERVAL_SEC
from utils.mock_state import advance_anomaly, get_mock_scenario_label
from utils.structured_logger import get_logger
from utils.ui_state import set_active_thread_id
from webhook.server import app as api_app

log = get_logger(__name__)


def run_api(host: str, port: int) -> None:
    uvicorn.run(api_app, host=host, port=port, log_level="info")


def main() -> None:
    settings = get_settings()
    api_app.state.graph = None

    api_thread = threading.Thread(
        target=run_api,
        kwargs={"host": settings.api_host, "port": settings.api_port},
        daemon=True,
    )
    api_thread.start()
    time.sleep(0.3)

    graph = None
    try:
        from agent.graph import build_graph

        graph = build_graph()
        api_app.state.graph = graph
        log.info("LangGraph compiled successfully.")
    except Exception:
        log.exception(
            "LangGraph failed to initialize (install deps: pip install -r requirements.txt). "
            "API still serves /health and /state."
        )

    log.info(
        "K8sWhisperer started: poll=%ss api=http://%s:%s health=/health state=/state "
        "slack=/slack/interactions dashboard_hitl=/slack/interactive",
        POLL_INTERVAL_SEC,
        settings.api_host,
        settings.api_port,
    )

    while True:
        if graph is None:
            time.sleep(5)
            continue

        thread_id = str(uuid.uuid4())
        set_active_thread_id(thread_id)
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
