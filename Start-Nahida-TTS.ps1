$ErrorActionPreference = "Stop"

$RootDir = $PSScriptRoot
$PythonPath = Join-Path $RootDir ".venv\Scripts\python.exe"
$ModelRoot = Join-Path $RootDir "genshin"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Python environment not found: $PythonPath"
}
if (-not (Test-Path -LiteralPath $ModelRoot)) {
    throw "Model directory not found: $ModelRoot"
}

$env:MODEL_PATH = $ModelRoot
$env:PYTHONIOENCODING = "utf-8"
Set-Location -LiteralPath $RootDir

& $PythonPath "nahida_webui.py"
