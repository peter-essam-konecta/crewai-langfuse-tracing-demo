param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{32}$')]
    [string]$TraceId,

    [string[]]$ExpectedTool = @(),

    [switch]$RequireFailureSummary,

    [string[]]$ExpectedCompositeChild = @(),

    [switch]$NoLegacyToolFallback,

    [switch]$Json
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
$envPath = Join-Path $repositoryRoot ".env"
if (!(Test-Path -LiteralPath $venvPython)) {
    throw "Missing .venv. Run .\scripts\setup.ps1 first."
}
if (!(Test-Path -LiteralPath $envPath)) {
    throw "Missing .env. Copy .env.example to .env first."
}

Get-Content -LiteralPath $envPath | ForEach-Object {
    $line = $_.Trim()
    if (!$line -or $line.StartsWith("#") -or !$line.Contains("=")) { return }
    $name, $value = $line -split "=", 2
    [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim().Trim('"').Trim("'"), "Process")
}

$requiredEnvironment = @("LANGFUSE_BASE_URL", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
$missingEnvironment = @($requiredEnvironment | Where-Object { ![Environment]::GetEnvironmentVariable($_, "Process") })
if ($missingEnvironment.Count -gt 0) {
    throw "Missing required Langfuse settings: $($missingEnvironment -join ', ')."
}

$baseUrl = $env:LANGFUSE_BASE_URL.TrimEnd("/")
$auth = [Convert]::ToBase64String(
    [Text.Encoding]::UTF8.GetBytes("$env:LANGFUSE_PUBLIC_KEY`:$env:LANGFUSE_SECRET_KEY")
)
$headers = @{ Authorization = "Basic $auth" }
$trace = Invoke-RestMethod `
    -Headers $headers `
    -Uri "$baseUrl/api/public/traces/$TraceId" `
    -TimeoutSec 30

$observations = @()
$page = 1
$pageSize = 100
do {
    $response = Invoke-RestMethod `
        -Headers $headers `
        -Uri "$baseUrl/api/public/observations?traceId=$TraceId&limit=$pageSize&page=$page" `
        -TimeoutSec 30
    $batch = @($response.data)
    $observations += $batch
    $page += 1
} while ($batch.Count -eq $pageSize)

$validatorArguments = @(
    "-m",
    "crewai_langfuse_demo.trace_validation",
    "--trace-id",
    $TraceId
)
foreach ($tool in $ExpectedTool) {
    $validatorArguments += @("--expected-tool", $tool)
}
if ($RequireFailureSummary) {
    $validatorArguments += "--require-failure-summary"
}
foreach ($child in $ExpectedCompositeChild) {
    $validatorArguments += @("--expected-composite-child", $child)
}
if ($NoLegacyToolFallback) {
    $validatorArguments += "--no-legacy-tool-fallback"
}

$env:PYTHONPATH = Join-Path $repositoryRoot "src"
$payloadJson = @{
    trace = $trace
    observations = $observations
} | ConvertTo-Json -Depth 40 -Compress
$reportJson = $payloadJson | & $venvPython @validatorArguments
if ($LASTEXITCODE -ne 0) {
    throw "Trace validation could not process the Langfuse API response."
}
$report = $reportJson | ConvertFrom-Json

if ($Json) {
    $reportJson
}
else {
    [pscustomobject]@{
        TraceId = $report.trace.id
        TraceName = $report.trace.name
        CanonicalRun = $report.trace.canonical_run_observation
        ObservationCount = $report.trace.observation_count
        Agents = @($report.agents) -join ", "
        FinalSchemaTools = @($report.tools.final_schema) -join ", "
        LegacyToolFallback = @($report.tools.legacy_fallback) -join ", "
        CanonicalGenerations = $report.canonical_generation_count
        SafeFailureSummaries = $report.failure_summaries.count
        FailureSummaryTools = @($report.failure_summaries.tools) -join ", "
        FailureErrorTypes = @($report.failure_summaries.error_types) -join ", "
        CompositeChildOperations = @($report.composite_children) -join ", "
        StructuralCoverage = "$($report.validation.passed_count) / $($report.validation.total_count) ($($report.validation.coverage_percent)%)"
    } | Format-List

    "Required application context on the canonical run:"
    $report.required_application_context | Format-List

    "Structural checks the Langfuse API can prove:"
    $report.validation.checks |
        Select-Object @{ Name = "Pass"; Expression = { if ($_.passed) { "YES" } else { "NO" } } }, description, detail |
        Format-Table -AutoSize -Wrap

    "SpanKind validation:"
    [pscustomobject]@{
        CanonicalGenerations = "$($report.span_kind.canonical_generations.status) (expected CLIENT)"
        CanonicalTools = "$($report.span_kind.canonical_tools.status) (expected INTERNAL)"
    } | Format-List

    "Validation boundaries:"
    $report.boundaries | Format-List

    if (@($report.warnings).Count -gt 0) {
        "Warnings:"
        @($report.warnings) | ForEach-Object { "- $_" }
    }
    if (@($report.validation.failures).Count -gt 0) {
        "Validation failures:"
        @($report.validation.failures) | ForEach-Object { "- $($_.description): $($_.detail)" }
    }
}

if (!$report.validation.passed) {
    exit 1
}
