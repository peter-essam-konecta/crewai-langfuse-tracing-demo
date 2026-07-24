$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"

if (!(Test-Path $venvPython)) {
    python -m venv (Join-Path $repositoryRoot ".venv")
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $repositoryRoot "requirements.txt")

Write-Host "Setup complete. Next: copy .env.example to .env, then run .\scripts\run-basic.ps1"

