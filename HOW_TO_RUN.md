# K8sWhisperer — How to Run Guide

## Overview
K8sWhisperer is an autonomous Kubernetes troubleshooting agent built with LangGraph, MCP servers, and LLM reasoning. This guide explains how to run the project from scratch.

## Prerequisites
- Python 3.8 or higher
- Windows/Linux/Mac with terminal access
- Internet connection (for dependencies)

## Step 1: Project Setup

### Navigate to Project Directory
```bash
cd c:\Users\Admin\OneDrive\Desktop\K8sWhisperer_demo
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Verify Installation
```bash
python --version
# Should show Python 3.x

python -c "import langgraph, pydantic; print('Dependencies OK')"
```

## Step 2: Environment Configuration

### Create .env File
Create a file named `.env` in the project root with:

```bash
# Use mock cluster for testing (recommended)
MOCK_CLUSTER=1

# LLM Configuration (use mock for demo, gemini for real AI)
LLM_PROVIDER=mock

# For Gemini API (Google AI Studio)
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=your-gemini-api-key-here
# GEMINI_MODEL=gemini-2.0-flash-exp

# For OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-openai-key
# OPENAI_MODEL=gpt-4o-mini

# For Anthropic
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# API Settings
API_HOST=0.0.0.0
API_PORT=8080

# Slack Integration (optional)
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_ID=C1234567890
SLACK_SIGNING_SECRET=your-signing-secret

# Persistence (optional - defaults shown)
AUDIT_LOG_PATH=audit_log.json
STATE_STORE_PATH=data/state_store.json
```

**Important:** Replace `your-gemini-api-key-here` with your actual Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey).
```

### Alternative: Set Environment Variables Directly
```bash
set MOCK_CLUSTER=1
set LLM_PROVIDER=gemini
set GEMINI_API_KEY=your-gemini-api-key-here
set GEMINI_MODEL=gemini-2.0-flash-exp
set API_HOST=0.0.0.0
set API_PORT=8080
set SLACK_BOT_TOKEN=xoxb-your-token
set SLACK_CHANNEL_ID=C1234567890
set SLACK_SIGNING_SECRET=your-secret
set AUDIT_LOG_PATH=audit_log.json
set STATE_STORE_PATH=data/state_store.json
```

## Step 3: Test MCP Servers (Optional)

### kubectl MCP Test
```bash
python -c "
from mcp_servers.kubectl_mcp import get_kubectl_client
k = get_kubectl_client()
print('kubectl MCP Health:', k.health())
print('Sample pods:', len(k.get_pods_all_namespaces()[:5]))
"
```

### Prometheus MCP Test
```bash
python -c "
from mcp_servers.prometheus_mcp import PrometheusMCP
p = PrometheusMCP()
print('Prometheus MCP Health:', p.health())
"
```

### Slack MCP Test
```bash
python -c "
from mcp_servers.slack_mcp import get_slack_client
s = get_slack_client()
print('Slack MCP Health:', s.health())
"
```

### Send Test Slack Message
```bash
python -c "
from mcp_servers.slack_mcp import get_slack_client
s = get_slack_client()
s.post_plain_text('YOUR_CHANNEL_ID', 'Hello from K8sWhisperer! 🚀')
print('Test message sent to Slack!')
"
```

## Step 4: Run the Project

### Start the System
```bash
python main.py
```

### Expected Startup Logs
```
INFO:K8sWhisperer started: poll=30s api=http://0.0.0.0:8080 health=/health slack=/slack/interactions
INFO:Observe cycle abc123...: events=10 pods=5 nodes=1
```

### System Behavior
- Runs in a continuous loop
- Polls cluster every 30 seconds
- Automatically detects and handles anomalies
- Logs all activities to console and audit_log.json

## Step 5: Monitor System Health

### Check API Health
```bash
# In another terminal
curl http://localhost:8080/health
# Expected: {"status": "ok"}
```

### Watch Logs in Real-Time
```bash
# In another terminal
python main.py 2>&1 | findstr "INFO"
# Or: python main.py 2>&1 | grep "INFO" (Linux/Mac)
```

## Step 6: Observe Anomaly Detection

With MOCK_CLUSTER=1, the system automatically simulates and handles anomalies. Watch for these log patterns:

### CrashLoopBackOff (Auto-Fix)
```
INFO:Rule-based plan selected for anomaly: CrashLoopBackOff
INFO:Plan: action=restart_pod blast=low
INFO:Execute: kubectl delete pod output: Mock deleted pod
INFO:Audit: Pod crashloop detected and auto-resolved
```

### OOMKilled (HITL Required)
```
INFO:Rule-based plan selected for anomaly: OOMKilled
INFO:Plan: action=patch_resource_limits blast=low
INFO:Safety gate: requires approval (resource change)
INFO:Slack: Interactive message sent for approval
```

### Pending Pod (Alert Only)
```
INFO:Rule-based plan selected for anomaly: PendingPod
INFO:Plan: action=alert_human blast=medium
INFO:Alert decision: should_alert=True (resource issue)
INFO:Slack: Pod stuck in Pending - check node capacity
```

### ImagePullBackOff (Alert Only)
```
INFO:Rule-based plan selected for anomaly: ImagePullBackOff
INFO:Plan: action=alert_human blast=low
INFO:Alert decision: should_alert=True (registry issue)
INFO:Slack: Container cannot pull image
```

### CPU Throttling (Auto-Fix)
```
INFO:CPU throttling detected: rate=0.7
INFO:Rule-based plan selected for anomaly: CPUThrottling
INFO:Plan: action=patch_resource_limits blast=medium
INFO:Execute: Patched deployment CPU (+50%)
```

### Evicted Pod (Auto-Cleanup)
```
INFO:Rule-based plan selected for anomaly: EvictedPod
INFO:Plan: action=delete_pod blast=low
INFO:Execute: kubectl delete pod (cleanup)
```

### Deployment Stalled (HITL)
```
INFO:Rule-based plan selected for anomaly: DeploymentStalled
INFO:Plan: action=alert_human blast=high
INFO:Safety gate: HITL required (high impact)
INFO:Slack: Deployment stalled - decide rollback/force
```

### Node NotReady (Critical Alert)
```
INFO:Rule-based plan selected for anomaly: NodeNotReady
INFO:Plan: action=alert_human blast=critical
INFO:Alert decision: should_alert=True (CRITICAL)
INFO:Slack: 🚨 Node failure - investigate immediately
```

## Step 7: Verify Results

### Check Audit Logs
```bash
# View complete audit trail
type audit_log.json
# Or: cat audit_log.json (Linux/Mac)

# Expected format:
[
  {
    "timestamp": "2026-03-30T...",
    "phase": "explain",
    "summary": "Anomaly detected and resolved",
    "action_taken": "kubectl delete pod output: ..."
  }
]
```

### Check Specific Anomalies
```bash
# Search for specific anomaly
findstr "CrashLoopBackOff" audit_log.json
```

## Step 8: Stop the System

### Graceful Shutdown
- Press `Ctrl+C` in the terminal running `python main.py`
- System will log shutdown and save final state

## Advanced Usage

### Real Kubernetes Cluster
```bash
# Remove MOCK_CLUSTER=1
# Ensure kubectl is configured
kubectl get nodes
kubectl get pods -A

# Install Prometheus (optional)
kubectl apply -f k8s/prometheus.yaml

# Run normally
python main.py
```

### Custom Anomalies
- Modify `agent/rule_detector.py` for new detection rules
- Update `agent/rule_engine.py` for new planning logic

### Debugging
```bash
# Enable debug logs
set PYTHONPATH=%CD%
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python main.py
```

## Troubleshooting

### Import Errors
```bash
pip install pydantic pydantic-settings langchain langchain-core langgraph requests slack-sdk
```

### Port Already in Use
```bash
set API_PORT=8001
python main.py
```

### No Anomalies Detected
- Ensure MOCK_CLUSTER=1 is set
- Wait 30+ seconds for polling cycle
- Check logs for "Observe cycle" messages

### LLM Errors
- Use LLM_PROVIDER=mock for testing
- For Gemini: Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey) and set GEMINI_API_KEY
- For OpenAI: Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- For Anthropic: Get API key from [Anthropic Console](https://console.anthropic.com/)
- Check API keys are set correctly in .env
- Test LLM loading: `python -c "from agent.llm_factory import get_chat_model; print(type(get_chat_model()).__name__)"`

### Slack Not Working
- Verify SLACK_BOT_TOKEN and SLACK_CHANNEL_ID
- Check Slack app permissions
- Ensure slack-sdk is installed: `pip install slack-sdk`
- Test MCP health with the Slack MCP Test above

## Demo Script

For presentations:

1. Start system: `python main.py`
2. Show logs: Point to anomaly detections
3. Show audit: Open `audit_log.json`
4. Show Slack: If configured, show alerts
5. Stop: `Ctrl+C`

## Architecture Overview

- **LangGraph**: Orchestrates the 7-stage pipeline
- **MCP Servers**: Abstract kubectl, Prometheus, Slack operations
- **Rule Engine**: Deterministic anomaly handling
- **Safety Gates**: Prevent dangerous auto-actions
- **HITL**: Human oversight for critical decisions

This system demonstrates autonomous DevOps with proper safety controls and human oversight.