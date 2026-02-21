$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
  throw ".venv is missing. Run setup first."
}

Push-Location $root
try {
  & $venvPython -m http.server 8090
}
finally {
  Pop-Location
}
