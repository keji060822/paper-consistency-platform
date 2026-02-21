$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiDir = Join-Path $root "api"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
  throw ".venv is missing. Run setup first."
}

Push-Location $apiDir
try {
  & $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --env-file .env
}
finally {
  Pop-Location
}

