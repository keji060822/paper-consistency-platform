$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root "runlogs\pids.txt"

function Get-ChildProcessIds {
  param([int]$ParentId)
  $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$ParentId" -ErrorAction SilentlyContinue
  foreach ($child in $children) {
    $childId = [int]$child.ProcessId
    $childId
    Get-ChildProcessIds -ParentId $childId
  }
}

if (-not (Test-Path $pidFile)) {
  Write-Output "No PID file found."
  exit 0
}

Get-Content $pidFile | ForEach-Object {
  if ($_ -match "PID:\s*(\d+)") {
    $procId = [int]$Matches[1]
    $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if ($proc) {
      $allIds = @($procId) + @(Get-ChildProcessIds -ParentId $procId)
      $allIds = $allIds | Sort-Object -Unique -Descending
      foreach ($id in $allIds) {
        $target = Get-Process -Id $id -ErrorAction SilentlyContinue
        if ($target) {
          Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
          Write-Output "Stopped PID $id"
        }
      }
    }
  }
}

$listenerIds = @()
$listenerIds += netstat -ano | Select-String "LISTENING" | Select-String ":8000|:8090" | ForEach-Object {
  ($_ -split "\s+")[-1]
}
$listenerIds = $listenerIds | Where-Object { $_ -match "^\d+$" } | Sort-Object -Unique
foreach ($rawId in $listenerIds) {
  $id = [int]$rawId
  $target = Get-Process -Id $id -ErrorAction SilentlyContinue
  if ($target -and $target.ProcessName -like "python*") {
    Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
    Write-Output "Stopped listener PID $id"
  }
}

Remove-Item $pidFile -Force
