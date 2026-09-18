param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Text,

    [string]$OutputPath,

    [int]$MaxChars = 90,

    [double]$Temperature = 0.65,

    [int]$TopK = 50
)

$ErrorActionPreference = "Stop"
$RootDir = $PSScriptRoot
$PythonPath = Join-Path $RootDir ".venv\Scripts\python.exe"
$ScriptPath = Join-Path $RootDir "nahida_tts.py"

if (-not $OutputPath) {
    $OutputPath = Join-Path $RootDir "outputs\nahida_cli.wav"
}

$env:PYTHONIOENCODING = "utf-8"
& $PythonPath $ScriptPath `
    --text $Text `
    --output $OutputPath `
    --max-chars $MaxChars `
    --temperature $Temperature `
    --top-k $TopK

if ($LASTEXITCODE -ne 0) {
    throw "Nahida TTS generation failed."
}

Write-Host "Created: $OutputPath"
