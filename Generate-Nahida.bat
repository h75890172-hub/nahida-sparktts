@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Generate-Nahida.ps1" %*
if errorlevel 1 pause
