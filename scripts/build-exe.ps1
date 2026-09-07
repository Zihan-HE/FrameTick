<#!
.SYNOPSIS
Build a portable Windows executable for TimeLapse Capture.

.DESCRIPTION
Uses the active Python interpreter and PyInstaller. Run after installing the
development dependencies listed in requirements-dev.txt.
#>

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    $python = 'python'
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name FrameTick `
    --icon assets/frametick.ico `
    --collect-all imageio `
    --collect-all imageio_ffmpeg `
    --hidden-import imageio.plugins.ffmpeg `
    --hidden-import imageio.plugins.pillow `
    --hidden-import pystray._win32 `
    --hidden-import win32con `
    --hidden-import win32gui `
    --paths src `
    src/launcher.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host "Built: $projectRoot\dist\FrameTick\FrameTick.exe"
