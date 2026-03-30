# K8sWhisperer — Runbook

## Prerequisites

- Python 3.10+
- **Either** a real cluster: `kubectl` on `PATH` and a working kubeconfig (e.g. minikube), **or** set **`MOCK_CLUSTER=1`** in `.env` to run the full pipeline against an in-memory fixture (no kube-apiserver, no `kubectl` binary). With mock mode, **each 30s cycle** presents the next of **eight** scenarios (CrashLoop, OOM, Pending, Evicted, ImagePull, NodeNotReady, DeploymentStalled, CPU throttle); after each full graph run the index advances automatically.

### Windows: `kubectl` not found

- Install CLI: `winget install -e --id Kubernetes.kubectl`, **or** run `powershell -ExecutionPolicy Bypass -File scripts/download_kubectl.ps1` (installs `tools/kubectl.exe`; the app auto-detects it), **or** rely on **`MOCK_CLUSTER=1`** for demos.
- Use **`py -3`** instead of **`python`** if the Microsoft Store stub appears.

### Quick run without a cluster

```powershell
.\scripts\run_with_mock_cluster.ps1
```

(Ensure `.env` has `MOCK_CLUSTER=1` or the script sets it.)
- For real LLM calls: an OpenAI or Anthropic API key
- Optional: Slack app with Bot token, Signing secret, and Interactivity Request URL pointing at this service

## Install

From the repository root:

```bash
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

Run each line separately. If you paste `install ... ".[dev]"` and `python main.py` on one line, pip may try to install a package literally named `python` and fail.

If editable install fails on older pip, use:

```bash
python -m pip install .
```

Or set `PYTHONPATH` to the repo root and install dependencies from `pyproject.toml` manually.

## Configure

Copy `.env.example` to `.env` and set at least:

- `LLM_PROVIDER=openai` and `OPENAI_API_KEY=...` (or `anthropic` + `ANTHROPIC_API_KEY`)
- For demos without API spend: `LLM_PROVIDER=mock` (deterministic stub responses)
- With a real provider (`gemini`, `openai`, `anthropic`), the app retries transient errors (429, overload, short 5xx) with backoff and uses the provider’s `max_retries`. **Daily free-tier caps** (e.g. Gemini `GenerateRequestsPerDay`) are not fixable by retrying; raise limits or switch model/key.
- **`MOCK_CLUSTER=1`:** Detection uses **rules + mock Prometheus only** (the Gemini/OpenAI classifier is skipped) so each 30s cycle shows anomalies immediately. Diagnose / explain / alert use lightweight mock templates too, so you can keep `LLM_PROVIDER=gemini` for future real-cluster use without blocking the demo loop.

## Run the agent loop + API

```bash
python main.py
```

This starts:

- A FastAPI server on `API_HOST`/`API_PORT` (default `0.0.0.0:8080`)
- A polling loop every 30 seconds that runs the LangGraph pipeline: Observe → Detect → Diagnose → Plan → Safety gate → Execute or HITL → Explain & audit log

Health check: `GET http://localhost:8080/health`

Slack interactivity (resume after HITL): `POST http://localhost:8080/slack/interactions`

## Slack HITL

1. Create a Slack app; enable Interactivity and set the Request URL to `https://<public-host>/slack/interactions` (use ngrok or similar for local dev).
2. Set `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, and `SLACK_CHANNEL_ID` in `.env`.
3. When the safety gate routes to HITL, the graph interrupts until Slack sends Approve/Reject; duplicate interactions are deduped via `data/state_store.json`.

## Audit log

Plain-English entries are appended to `audit_log.json` (override with `AUDIT_LOG_PATH`).

## Tests

```bash
python -m pytest tests -q
```

Integration tests that touch a real cluster are gated with `K8S_WHISPERER_INTEGRATION=1`.

## Kubernetes RBAC

See `k8s/rbac.yml` for a least-privilege-oriented starting point; tighten further for production.
