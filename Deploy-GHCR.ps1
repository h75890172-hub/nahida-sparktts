param(
    [ValidateSet("up", "down", "logs", "pull")]
    [string]$Action = "up"
)

$ErrorActionPreference = "Stop"
$RootDir = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$KnownGhPath = Join-Path $env:LOCALAPPDATA `
    "Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe"

$ghCommand = Get-Command gh -ErrorAction SilentlyContinue
$GhPath = if ($ghCommand) { $ghCommand.Source } else { $KnownGhPath }
if (-not (Test-Path -LiteralPath $GhPath)) {
    throw "GitHub CLI is not installed."
}

Set-Location -LiteralPath $RootDir

if ($Action -in @("up", "pull")) {
    $env:HTTPS_PROXY = "http://127.0.0.1:7897"
    $env:HTTP_PROXY = "http://127.0.0.1:7897"

    $token = & $GhPath auth token --hostname github.com
    if ($LASTEXITCODE -ne 0 -or -not $token) {
        throw "Unable to read the GitHub token."
    }

    $token | docker login ghcr.io --username project-maintainer --password-stdin
    if ($LASTEXITCODE -ne 0) {
        & $GhPath auth refresh --hostname github.com --scopes read:packages
        if ($LASTEXITCODE -ne 0) {
            throw "GitHub authentication refresh failed."
        }
        $token = & $GhPath auth token --hostname github.com
        $token | docker login ghcr.io --username project-maintainer --password-stdin
        if ($LASTEXITCODE -ne 0) {
            throw "GHCR login failed."
        }
    }
}

switch ($Action) {
    "up" {
        docker compose -f docker-compose.ghcr.yml up -d
    }
    "down" {
        docker compose -f docker-compose.ghcr.yml down
    }
    "logs" {
        docker compose -f docker-compose.ghcr.yml logs -f --tail 200
    }
    "pull" {
        docker pull ghcr.io/project-maintainer/nahida-sparktts:main
    }
}
