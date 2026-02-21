$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$apiDir = Join-Path $root "api"
$backendOut = Join-Path $root "runlogs\backend.out.log"
$backendErr = Join-Path $root "runlogs\backend.err.log"
$frontendOut = Join-Path $root "runlogs\frontend.out.log"
$frontendErr = Join-Path $root "runlogs\frontend.err.log"

New-Item -ItemType Directory -Force -Path (Join-Path $root "runlogs") | Out-Null
if (-not (Test-Path $venvPython)) {
  throw ".venv is missing. Run setup first."
}

$backend = Start-Process -FilePath $venvPython `
  -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --env-file .env" `
  -WorkingDirectory $apiDir `
  -PassThru `
  -WindowStyle Hidden `
  -RedirectStandardOutput $backendOut `
  -RedirectStandardError $backendErr

$frontend = Start-Process -FilePath $venvPython `
  -ArgumentList "-m http.server 8090" `
  -WorkingDirectory $root `
  -PassThru `
  -WindowStyle Hidden `
  -RedirectStandardOutput $frontendOut `
  -RedirectStandardError $frontendErr

"Backend PID: $($backend.Id)" | Out-File -Encoding UTF8 (Join-Path $root "runlogs\pids.txt")
"Frontend PID: $($frontend.Id)" | Out-File -Encoding UTF8 -Append (Join-Path $root "runlogs\pids.txt")

Write-Output "Backend PID: $($backend.Id)"
Write-Output "Frontend PID: $($frontend.Id)"
Write-Output "Logs: $backendOut, $backendErr, $frontendOut, $frontendErr"
