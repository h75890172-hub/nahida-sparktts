param(
    [string]$RepositoryName = "nahida-sparktts",

    [ValidateSet("private", "public")]
    [string]$Visibility = "private"
)

$ErrorActionPreference = "Stop"
$RootDir = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$KnownGhPath = Join-Path $env:LOCALAPPDATA `
    "Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe"

$ghCommand = Get-Command gh -ErrorAction SilentlyContinue
if ($ghCommand) {
    $GhPath = $ghCommand.Source
} elseif (Test-Path -LiteralPath $KnownGhPath) {
    $GhPath = $KnownGhPath
} else {
    throw "GitHub CLI is not installed."
}

Set-Location -LiteralPath $RootDir

if (git status --porcelain) {
    throw "The Git working tree is not clean. Commit changes before pushing."
}

& $GhPath auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

$remote = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0 -and $remote) {
    git push -u origin main
} else {
    & $GhPath repo create $RepositoryName "--$Visibility" --source . --remote origin --push
}

Write-Host "GitHub repository operation completed."
