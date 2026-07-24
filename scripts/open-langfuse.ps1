$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$envPath = Join-Path $repositoryRoot ".env"
if (!(Test-Path $envPath)) {
    throw "Missing .env. Copy .env.example to .env first."
}

$langfuseUrl = (Get-Content $envPath | Where-Object { $_ -match '^\s*LANGFUSE_BASE_URL\s*=' } | Select-Object -First 1) -replace '^\s*LANGFUSE_BASE_URL\s*=\s*', ''
if (!$langfuseUrl) {
    throw "LANGFUSE_BASE_URL is missing from .env."
}

Start-Process $langfuseUrl.Trim().Trim('"').Trim("'")
Write-Host "Opened Langfuse in your default browser. Open the newest trace for this demo service."

