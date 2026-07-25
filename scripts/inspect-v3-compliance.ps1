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

foreach ($name in "LANGFUSE_BASE_URL", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY") {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name, "Process"))) {
        throw "Missing $name in .env."
    }
}

function Get-TraceAttribute {
    param(
        [object]$Observation,
        [string]$Name
    )

    $attributes = $Observation.metadata.attributes
    if ($null -eq $attributes) { return $null }
    $property = $attributes.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

$baseUrl = $env:LANGFUSE_BASE_URL.TrimEnd("/")
$auth = [Convert]::ToBase64String(
    [Text.Encoding]::UTF8.GetBytes("$env:LANGFUSE_PUBLIC_KEY`:$env:LANGFUSE_SECRET_KEY")
)
$headers = @{ Authorization = "Basic $auth" }
$trace = Invoke-RestMethod -Headers $headers -Uri "$baseUrl/api/public/traces/$TraceId"
$observations = @()
foreach ($page in 1, 2) {
    $response = Invoke-RestMethod -Headers $headers -Uri "$baseUrl/api/public/observations?traceId=$TraceId&limit=100&page=$page"
    $observations += @($response.data)
}

$generations = @($observations | Where-Object { $_.name -eq "chat demo-groq" })
$proxyRequests = @($observations | Where-Object { $_.name -eq "POST /v1/chat/completions" })
$costChecks = @(
    $generations | ForEach-Object {
        $legacyCost = Get-TraceAttribute -Observation $_ -Name "litellm.cost.total"
        $v3Cost = Get-TraceAttribute -Observation $_ -Name "gen_ai.usage.cost"
        $matches = $false
        if ($null -ne $legacyCost -and $null -ne $v3Cost) {
            $matches = [Math]::Abs(([double]$legacyCost) - ([double]$v3Cost)) -lt 0.000000001
        }
        [pscustomobject]@{ legacyCost = $legacyCost; v3Cost = $v3Cost; matches = $matches }
    }
)

$checks = @(
    [pscustomobject]@{ Check = "Trace was found"; Pass = ($null -ne $trace) },
    [pscustomobject]@{ Check = "Canonical model generations found"; Pass = ($generations.Count -gt 0) },
    [pscustomobject]@{ Check = "Proxy and model generation counts match"; Pass = ($generations.Count -gt 0 -and $generations.Count -eq $proxyRequests.Count) },
    [pscustomobject]@{ Check = "Every generation has matching V3 cost"; Pass = ($costChecks.Count -eq $generations.Count -and @($costChecks | Where-Object { -not $_.matches }).Count -eq 0) }
)
$passedChecks = @($checks | Where-Object Pass).Count

[pscustomobject]@{
    traceId = $TraceId
    rootName = $trace.name
    canonicalGenerationCount = $generations.Count
    proxyRequestCount = $proxyRequests.Count
    costChecks = $costChecks
    passedChecks = $passedChecks
    totalChecks = $checks.Count
    v3CostReady = ($passedChecks -eq $checks.Count)
    notVerifiableFromLangfusePublicApi = @("OpenTelemetry SpanKind")
    checks = $checks
} | ConvertTo-Json -Depth 6
