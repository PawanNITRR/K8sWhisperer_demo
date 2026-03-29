# Downloads kubectl.exe into repo tools/ (Windows amd64). Run: powershell -ExecutionPolicy Bypass -File scripts/download_kubectl.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$tools = Join-Path $root "tools"
New-Item -ItemType Directory -Force -Path $tools | Out-Null
$stable = (Invoke-RestMethod -Uri "https://dl.k8s.io/release/stable.txt").Trim()
$uri = "https://dl.k8s.io/release/$stable/bin/windows/amd64/kubectl.exe"
$dest = Join-Path $tools "kubectl.exe"
Write-Host "Downloading $uri -> $dest"
Invoke-WebRequest -Uri $uri -OutFile $dest -UseBasicParsing
Write-Host "Done. Add tools to PATH or set KUBECTL_PATH=$dest"
