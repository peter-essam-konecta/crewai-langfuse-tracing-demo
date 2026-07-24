$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
if (!(Test-Path $venvPython)) {
    throw "Missing .venv. Run .\scripts\setup.ps1 first."
}

$env:PYTHONPATH = (Join-Path $repositoryRoot "src")
Push-Location $repositoryRoot
try {
    & $venvPython -m unittest discover -s tests
}
finally {
    Pop-Location
}

