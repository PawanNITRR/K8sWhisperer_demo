from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from utils.ui_state import build_state_payload
from webhook.handlers import dashboard_hitl_interactive, slack_interactions

app = FastAPI(title="K8sWhisperer API")

_settings = get_settings()
_origins = [o.strip() for o in _settings.cors_origins.split(",") if o.strip()]
# Local Vite may use any port; regex covers localhost / 127.0.0.1 with optional port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins if _origins else ["http://localhost:5173"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/state")
def state(request: Request) -> dict:
    """Latest graph snapshot + audit log for the React dashboard."""
    graph = getattr(request.app.state, "graph", None)
    return build_state_payload(graph, get_settings())


@app.post("/slack/interactions")
async def slack_interactions_route(request: Request):
    return await slack_interactions(request)


@app.post("/slack/interactive")
async def dashboard_slack_interactive_route(request: Request):
    """Dashboard approve/reject (JSON); Slack uses /slack/interactions with form body."""
    return await dashboard_hitl_interactive(request)
