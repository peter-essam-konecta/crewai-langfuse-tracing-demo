$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$proxyVenv = Join-Path $repositoryRoot ".proxy-venv"
$proxyPython = Join-Path $proxyVenv "Scripts\python.exe"

if (!(Test-Path $proxyPython)) {
    python -m venv $proxyVenv
}

& $proxyPython -m pip install --upgrade pip
& $proxyPython -m pip install -r (Join-Path $repositoryRoot "requirements-proxy.txt")

Write-Host "LiteLLM Proxy setup complete. Next: run .\scripts\start-litellm-proxy.ps1 or .\scripts\start-v3-cloud-proxy.ps1"
