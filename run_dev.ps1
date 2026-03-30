# K8sWhisperer — local demo (mock cluster + mock LLM + API + agent loop)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:MOCK_CLUSTER = "1"
$env:LLM_PROVIDER = "mock"
# Optional: uncomment if not using mock cluster but want UI approve/reject
# $env:DASHBOARD_HITL = "1"

Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
py -3 -m pip install -r requirements.txt

Write-Host "Starting backend (Ctrl+C to stop). Open a second terminal for the UI: cd K8sWhisperer_New; npm install; npm run dev" -ForegroundColor Green
py -3 main.py
