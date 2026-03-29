# Run agent with in-memory cluster (no kube-apiserver). Uses .env for LLM keys.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
$env:MOCK_CLUSTER = "1"
$env:PYTHONPATH = (Get-Location).Path
Write-Host "MOCK_CLUSTER=1 — using fake CrashLoop pod. Press Ctrl+C to stop."
py -3 main.py
