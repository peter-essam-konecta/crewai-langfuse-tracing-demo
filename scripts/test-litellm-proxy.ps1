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

$masterKey = $env:LITELLM_MASTER_KEY.Trim()
if ($masterKey.StartsWith("Bearer ")) {
    $masterKey = $masterKey.Substring(7).Trim()
}

$modelName = if ($env:LITELLM_MODEL) { $env:LITELLM_MODEL -replace '^openai/', '' } else { "gemini-2.5-flash-nothink" }

$headers = @{
    Authorization = "Bearer $masterKey"
    "Content-Type" = "application/json"
}
$body = @{
    model = $modelName
    messages = @(@{ role = "user"; content = "Reply only: LiteLLM Proxy is connected." })
} | ConvertTo-Json -Depth 4
$url = "$($env:LITELLM_PROXY_HOST.TrimEnd('/'))/v1/chat/completions"

Write-Host "Sending a safe smoke test to $url (model: $modelName)"
$response = Invoke-RestMethod -Method Post -Uri $url -Headers $headers -Body $body
Write-Host "LiteLLM Proxy response:"
Write-Host $response.choices[0].message.content

