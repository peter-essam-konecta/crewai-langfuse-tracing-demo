$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$proxyVenv = Join-Path $repositoryRoot ".proxy-venv"
$proxyPython = Join-Path $proxyVenv "Scripts\python.exe"

if (!(Test-Path $proxyPython)) {
    python -m venv $proxyVenv
    if ($LASTEXITCODE -ne 0) { throw "Failed to create the LiteLLM Proxy Python environment." }
}

& $proxyPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip in the LiteLLM Proxy environment." }
& $proxyPython -m pip install -r (Join-Path $repositoryRoot "requirements-proxy.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install the LiteLLM Proxy requirements." }

Write-Host "LiteLLM Proxy setup complete. Next: run .\scripts\start-litellm-proxy.ps1 or .\scripts\start-v3-cloud-proxy.ps1"
