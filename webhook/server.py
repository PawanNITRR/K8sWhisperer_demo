from __future__ import annotations

from fastapi import FastAPI, Request

from webhook.handlers import slack_interactions

app = FastAPI(title="K8sWhisperer API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/slack/interactions")
async def slack_interactions_route(request: Request):
    return await slack_interactions(request)
