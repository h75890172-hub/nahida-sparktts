@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Push-To-GitHub.ps1" %*
if errorlevel 1 pause
