$ErrorActionPreference = "Stop"

$listener = Get-NetTCPConnection -LocalPort 7861 -State Listen -ErrorAction SilentlyContinue

if (-not $listener) {
    Write-Host "Nahida TTS WebUI is not running."
    exit 0
}

foreach ($connection in $listener) {
    $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
    if (-not $process -or $process.ProcessName -ne "python") {
        throw "Port 7861 is owned by a non-Python process."
    }
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($process.Id)"
    if (-not $processInfo.CommandLine -or -not $processInfo.CommandLine.Contains("nahida_webui.py")) {
        throw "Refusing to stop Python process that is not the Nahida WebUI."
    }
    Stop-Process -Id $process.Id -Force
    Write-Host "Stopped WebUI process $($process.Id)."
}
