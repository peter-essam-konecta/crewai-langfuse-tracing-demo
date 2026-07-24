param(
    [Parameter(Mandatory = $true)]
    [string]$TraceId
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$envPath = Join-Path $repositoryRoot ".env"
if (!(Test-Path $envPath)) {
    throw "Missing .env. Copy .env.example to .env first."
}

Get-Content $envPath | ForEach-Object {
    $line = $_.Trim()
    if (!$line -or $line.StartsWith("#") -or !$line.Contains("=")) { return }
    $name, $value = $line -split "=", 2
    [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim().Trim('"').Trim("'"), "Process")
}

$baseUrl = $env:LANGFUSE_BASE_URL.TrimEnd("/")
$auth = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("$env:LANGFUSE_PUBLIC_KEY`:$env:LANGFUSE_SECRET_KEY"))
$headers = @{ Authorization = "Basic $auth" }
$trace = Invoke-RestMethod -Headers $headers -Uri "$baseUrl/api/public/traces/$TraceId"
$observations = (Invoke-RestMethod -Headers $headers -Uri "$baseUrl/api/public/observations?traceId=$TraceId&limit=100").data

[pscustomobject]@{
    TraceId = $TraceId
    RootName = $trace.name
    ObservationCount = @($observations).Count
    Agents = @($observations | Where-Object { $_.name -like 'invoke_agent *' } | Select-Object -ExpandProperty name -Unique)
    Tools = @($observations | Where-Object { $_.name -eq 'Tool Usage' } | ForEach-Object { $_.metadata.attributes.tool_name } | Where-Object { $_ } | Select-Object -Unique)
    ModelGenerations = @($observations | Where-Object { $_.type -eq 'GENERATION' }).Count
    SafeFailureSummaries = @($observations | Where-Object { $_.name -eq 'demo.failure_summary' }).Count
    CompositeChildOperations = @($observations | Where-Object { $_.name -like 'demo.composite.child.*' }).Count
} | Format-List

