param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("basic", "retry", "delegation", "composite-tool")]
    [string]$Scenario,

    [switch]$FailureAdapter,
    [switch]$CompositeAdapter
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
$envPath = Join-Path $repositoryRoot ".env"

if (!(Test-Path $venvPython)) {
    throw "Missing .venv. Run .\scripts\setup.ps1 first."
}
if (!(Test-Path $envPath)) {
    throw "Missing .env. Copy .env.example to .env and add your approved settings."
}

Get-Content $envPath | ForEach-Object {
    $line = $_.Trim()
    if (!$line -or $line.StartsWith("#") -or !$line.Contains("=")) { return }
    $name, $value = $line -split "=", 2
    [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim().Trim('"').Trim("'"), "Process")
}

$env:PYTHONUTF8 = "1"
$env:PYTHONPATH = (Join-Path $repositoryRoot "src")
$arguments = @("-m", "crewai_langfuse_demo.main", $Scenario)
if ($FailureAdapter) { $arguments += "--failure-adapter" }
if ($CompositeAdapter) { $arguments += "--composite-adapter" }

Push-Location $repositoryRoot
try {
    & $venvPython @arguments
}
finally {
    Pop-Location
}

