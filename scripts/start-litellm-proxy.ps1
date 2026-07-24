param(
    [int]$Port = 4000
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$envPath = Join-Path $repositoryRoot ".env"
$configPath = Join-Path $repositoryRoot "litellm-proxy\config.yaml"
$venvPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
$litellmExe = Join-Path $repositoryRoot ".venv\Scripts\litellm.exe"

if (!(Test-Path $envPath)) {
    throw "Missing .env. Copy .env.example to .env first."
}
if (!(Test-Path $venvPython) -or !(Test-Path $litellmExe)) {
    throw "Missing LiteLLM environment. Run .\scripts\setup.ps1 first."
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
$env:OTEL_SERVICE_NAME = "crewai-langfuse-demo-proxy"
$env:OTEL_ENVIRONMENT_NAME = "development"
$env:OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT = "no_content"
$env:PYTHONUTF8 = "1"

Write-Host "Starting LiteLLM Proxy on http://127.0.0.1:$Port"
Write-Host "Route: demo-groq -> groq/llama-3.3-70b-versatile"
Write-Host "Model telemetry: LiteLLM Proxy -> Langfuse"
Write-Host "Press Ctrl+C to stop the Proxy."

& $litellmExe --config $configPath --host 127.0.0.1 --port $Port
