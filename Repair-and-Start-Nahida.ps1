$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$LogPath = Join-Path $RootDir "docker_repair.log"
$TaskName = "Codex-Nahida-Docker-Repair"
$DockerBin = "C:\Program Files\Docker\Docker\resources\bin"
$DockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"

function Write-Log {
    param([string]$Message)
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Message"
    Add-Content -LiteralPath $LogPath -Value $line -Encoding utf8
    Write-Host $line
}

function Test-DockerReady {
    $env:PATH = "$DockerBin;$env:PATH"
    & docker info *> $null
    return $LASTEXITCODE -eq 0
}

function Stop-DockerProcesses {
    Get-Process -Name 'Docker Desktop','com.docker.backend','com.docker.build',
        'docker-agent','docker','docker-desktop' -ErrorAction SilentlyContinue |
        Stop-Process -Force
}

function Move-DockerRuntime {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }
    $suffix = Get-Date -Format "yyyyMMddHHmmss"
    $target = "$Path.repair-$suffix"
    Move-Item -LiteralPath $Path -Destination $target
    Write-Log "Moved Docker runtime: $Path -> $target"
}

function Wait-ForDocker {
    for ($attempt = 1; $attempt -le 60; $attempt++) {
        if (Test-DockerReady) {
            return $true
        }
        Start-Sleep -Seconds 5
    }
    return $false
}

Write-Log "Starting unattended Docker repair and deployment."

if (-not (Test-DockerReady)) {
    Write-Log "Docker engine is unavailable. Resetting user runtime state."
    Stop-DockerProcesses
    & wsl.exe --shutdown *> $null
    Move-DockerRuntime (Join-Path $env:LOCALAPPDATA "Docker")
    Move-DockerRuntime (Join-Path $env:LOCALAPPDATA "docker-secrets-engine")
    Start-Process -FilePath $DockerDesktop `
        -WorkingDirectory (Split-Path -Parent $DockerDesktop)

    if (-not (Wait-ForDocker)) {
        throw "Docker engine did not become ready within five minutes."
    }
}

Write-Log "Docker engine is ready. Deploying the published GHCR image."
& (Join-Path $RootDir "Deploy-GHCR.ps1") -Action up
if ($LASTEXITCODE -ne 0) {
    throw "GHCR deployment failed."
}

Write-Log "Deployment completed successfully."
& schtasks.exe /Delete /TN $TaskName /F *> $null
