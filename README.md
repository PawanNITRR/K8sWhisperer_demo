# K8sWhisperer

Automated observation and remediation assistant for Kubernetes. The service runs a continuous control loop: collect cluster state, detect anomalies, produce a remediation plan, apply optional human approval, and execute vetted actions against the API server.

The workflow is implemented with *LangGraph. A **FastAPI* service ships alongside the agent for health checks, dashboard state, and Slack- or UI-driven human-in-the-loop (HITL) approvals.

---

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running](#running)
- [HTTP API](#http-api)
- [Repository layout](#repository-layout)
- [Testing](#testing)
- [Security](#security)

---

## Overview

K8sWhisperer is designed as a *bounded automation layer*: it focuses on well-defined failure patterns (for example CrashLoopBackOff, OOMKilled, image pull failures) and pairs deterministic rules with optional LLM assistance for detection, diagnosis, and planning where no rule applies.

Operations are gated by a *safety module* that considers confidence, blast radius, and policy (including actions and anomaly classes that must not run unattended).

---

## Features

| Area | Description |
|------|-------------|
| *Observation* | Aggregates pods, nodes, deployments, and events via kubectl (or an in-memory mock for demos). |
| *Detection* | Rule-based signals from Kubernetes resource JSON; optional LLM classification; optional Prometheus query for CPU throttling signals. |
| *Diagnosis* | kubectl describe / kubectl logs for the primary workload; optional LLM summarization and structured diagnosis. |
| *Planning* | Rule-driven remediation maps (e.g. memory bump for OOM); LLM fallback when no rule matches. |
| *Governance* | Safety gate and HITL path; audit log and configurable state store paths. |
| *Integration* | REST API for monitoring and approvals; optional Slack signing-verified interactions. |

---

## Architecture

High-level processing order (see agent/graph.py):


observe → detect → diagnose → plan → safety_gate → [execute | hitl → execute] → alert_decision → explain


- *Observe* — agent/nodes/observe.py — Builds a normalized cluster snapshot; optionally queries Prometheus.
- *Detect* — agent/nodes/detect.py, agent/rule_detector.py, agent/rule_engine.py (CPU throttling) — Produces primary_anomaly.
- *Diagnose* — agent/nodes/diagnose.py — Evidence gathering and optional LLM diagnosis.
- *Plan* — agent/nodes/plan.py, agent/rule_engine.py — Emits a RemediationPlan.
- *Safety / HITL* — agent/nodes/safety_gate.py, agent/nodes/hitl.py — Auto-execute vs approval.
- *Execute* — agent/nodes/execute.py — Dispatches to the kubectl adapter under mcp_servers/.

The *mcp_servers* package provides thin clients: subprocess-backed kubectl access, HTTP access to Prometheus, and a *mock* implementation for CI and demonstration without a live cluster.

The default observation interval is *30 seconds* (schemas/constants.py — POLL_INTERVAL_SEC).

---

## Requirements

- *Python* 3.10 or newer  
- *kubectl* configured against your target cluster (not required when MOCK_CLUSTER=1)  
- *Optional:* Prometheus reachable at PROMETHEUS_BASE_URL for throttle-based detection  
- *Optional:* API credentials for OpenAI, Anthropic, or Google Gemini when LLM_PROVIDER is not mock  

---

## Installation

bash
cd K8sWhisperer_demo
python -m venv .venv

(Clone the repository first if you obtained it from version control.)

Activate the virtual environment:

- *Windows (cmd):* .venv\Scripts\activate.bat
- *Windows (PowerShell):* .venv\Scripts\Activate.ps1
- *macOS / Linux:* source .venv/bin/activate

bash
pip install -r requirements.txt
cp .env.example .env   # or copy .env.example .env on Windows


Edit .env for your environment (see [Configuration](#configuration)).

---

## Configuration

Application settings load from environment variables and an optional .env file in the project root (see config.py).

| Variable | Purpose |
|----------|---------|
| MOCK_CLUSTER | 1 / true — use in-memory cluster fixture; no real API server. |
| LLM_PROVIDER | openai, anthropic, gemini, or mock. |
| OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY | Provider keys when applicable. |
| KUBECTL_PATH | Optional absolute path to kubectl if not on PATH. |
| KUBECTL_CONTEXT | Optional kubeconfig context name. |
| PROMETHEUS_BASE_URL | Optional; e.g. http://localhost:9090. |
| API_HOST, API_PORT | FastAPI bind address (default 0.0.0.0:8080). |
| SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_CHANNEL_ID | Optional Slack HITL. |
| DASHBOARD_HITL | Allow dashboard JSON approval endpoint (see .env.example). |
| CORS_ORIGINS | Comma-separated browser origins for the API. |
| AUDIT_LOG_PATH, STATE_STORE_PATH | Paths for audit and durable state. |

A annotated template is maintained in *.env.example*.

---

## Running

Start the agent and API:

bash
python main.py


Behavior:

- The *FastAPI* application listens on http://<API_HOST>:<API_PORT>.
- The *LangGraph* pipeline runs on a timer; each invocation uses a new thread_id for checkpoint isolation.

*Mock mode* (MOCK_CLUSTER=1, LLM_PROVIDER=mock): suitable for local demos without cluster credentials or external LLM usage.

*Production-style mode:* set MOCK_CLUSTER=0, ensure kubectl and kubeconfig are valid, and configure an LLM provider if you rely on non-rule paths.

*Dashboard:* the React application under K8sWhisperer_New/ is maintained separately; install dependencies with npm install and run the dev server per that package’s scripts, pointing the UI at the API base URL.

---

## HTTP API

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Liveness response ({"status":"ok"}). |
| GET | /state | Serialized agent state and audit information for the dashboard. |
| POST | /slack/interactions | Slack interaction payloads (form-encoded / signing verification). |
| POST | /slack/interactive | JSON approvals from the local dashboard when permitted by configuration. |

CORS is configured for local Vite-style origins; adjust CORS_ORIGINS as needed.

---

## Repository layout

| Path | Responsibility |
|------|----------------|
| main.py | Process entry: API thread, graph compilation, polling loop. |
| config.py | Pydantic settings. |
| agent/graph.py | LangGraph definition and routing. |
| agent/nodes/ | Graph node implementations. |
| agent/rule_detector.py | Deterministic anomaly detection from K8s objects. |
| agent/rule_engine.py | Remediation mapping and Prometheus-derived CPU throttling helper. |
| mcp_servers/ | Kubectl, Prometheus, and mock adapters. |
| webhook/ | FastAPI application and interaction handlers. |
| schemas/ | Enums, models, and shared constants. |
| utils/ | Logging, UI state, log chunking, mock scenario helpers. |
| K8sWhisperer_New/ | Frontend (Vite + React). |

---

## Testing

bash
pip install pytest
pytest


Run from the repository root.

---

## Security

- Treat *auto-execute* as privileged: scope Kubernetes RBAC, review schemas/constants.py for destructive actions and HITL-only anomaly sets, and align with organizational change policy before deployment.
- *Slack* endpoints rely on signing secret verification when configured; do not expose administrative interfaces without TLS and network controls in real environments.
- This project is a *reference / demonstration* codebase; production hardening (secrets management, authn/z on /state, rate limits, etc.) is the operator’s responsibility.

---

## License

No project-level license file is bundled here. Add a LICENSE file before redistribution if required.
