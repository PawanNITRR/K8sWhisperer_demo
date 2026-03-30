# K8sWhisperer — Vite dashboard (run backend first with run_dev.ps1)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "K8sWhisperer_New")

if (-not (Test-Path "node_modules")) {
    Write-Host "npm install..." -ForegroundColor Cyan
    npm install
}

Write-Host "Starting Vite at http://localhost:5173 (API default http://localhost:8080)" -ForegroundColor Green
npm run dev
