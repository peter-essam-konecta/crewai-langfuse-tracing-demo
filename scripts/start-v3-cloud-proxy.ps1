param(
    [int]$Port = 4002
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$envPath = Join-Path $repositoryRoot ".env"
$configPath = Join-Path $repositoryRoot "litellm-proxy\config.v3-cloud.yaml"
$proxyRoot = Join-Path $repositoryRoot "litellm-proxy"
$proxyPython = Join-Path $repositoryRoot ".proxy-venv\Scripts\python.exe"
$litellmExe = Join-Path $repositoryRoot ".proxy-venv\Scripts\litellm.exe"

if (!(Test-Path $envPath)) {
    throw "Missing .env. Copy .env.example to .env first."
}
if (!(Test-Path $proxyPython) -or !(Test-Path $litellmExe)) {
    throw "Missing LiteLLM Proxy environment. Run .\scripts\setup-litellm-proxy.ps1 first."
}

Get-Content $envPath | ForEach-Object {
    $line = $_.Trim()
    if (!$line -or $line.StartsWith("#") -or !$line.Contains("=")) { return }
    $name, $value = $line -split "=", 2
    [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim().Trim('"').Trim("'"), "Process")
}

foreach ($name in "GROQ_API_KEY", "LITELLM_MASTER_KEY", "LANGFUSE_BASE_URL", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY") {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name, "Process"))) {
        throw "Missing $name in .env."
    }
}

$env:LANGFUSE_HOST = $env:LANGFUSE_BASE_URL
$env:LITELLM_OTEL_V2 = "true"
$env:OTEL_SERVICE_NAME = "crewai-langfuse-demo-v3-cloud-proxy"
$env:OTEL_ENVIRONMENT_NAME = "development"
$env:OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT = "no_content"
$env:PYTHONPATH = "$proxyRoot;$env:PYTHONPATH"
$env:LITELLM_WORKER_STARTUP_HOOKS = "v3_cost_mapper:install"
$env:PYTHONUTF8 = "1"

Write-Host "Starting LiteLLM V3 Cloud Proxy on http://127.0.0.1:$Port"
Write-Host "Route: demo-groq -> groq/llama-3.3-70b-versatile"
Write-Host "Model telemetry: LiteLLM Proxy -> Langfuse Cloud with V3 cost"
Write-Host "Press Ctrl+C to stop the Proxy."

& $litellmExe --config $configPath --host 127.0.0.1 --port $Port
