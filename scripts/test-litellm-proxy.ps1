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

if ([string]::IsNullOrWhiteSpace($env:LITELLM_MASTER_KEY)) {
    throw "Missing LITELLM_MASTER_KEY in .env."
}

$headers = @{
    Authorization = "Bearer $env:LITELLM_MASTER_KEY"
    "Content-Type" = "application/json"
}
$body = @{
    model = "demo-groq"
    messages = @(@{ role = "user"; content = "Reply only: local LiteLLM Proxy is connected." })
} | ConvertTo-Json -Depth 4
$url = "$($env:LITELLM_PROXY_HOST.TrimEnd('/'))/v1/chat/completions"

Write-Host "Sending a safe smoke test to $url"
$response = Invoke-RestMethod -Method Post -Uri $url -Headers $headers -Body $body
Write-Host "LiteLLM Proxy response:"
Write-Host $response.choices[0].message.content

