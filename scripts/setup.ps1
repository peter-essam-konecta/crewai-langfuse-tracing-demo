$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"

if (!(Test-Path $venvPython)) {
    python -m venv (Join-Path $repositoryRoot ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Failed to create the application Python environment." }
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip in the application environment." }
& $venvPython -m pip install -r (Join-Path $repositoryRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install the application requirements." }

Write-Host "Setup complete. Next: copy .env.example to .env, then run .\scripts\run-basic.ps1"
