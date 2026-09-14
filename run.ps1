# AI Text Summarizer - PowerShell Quick Launcher
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($scriptDir) { Set-Location $scriptDir }

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  AI Text Summarizer - Quick Launcher" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[1/2] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "[2/2] Installing requirements..." -ForegroundColor Yellow
    .\.venv\Scripts\pip install -r requirements.txt
}

Write-Host "[INFO] Starting server and opening browser..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server.`n" -ForegroundColor DarkGray

& ".\.venv\Scripts\python.exe" "Text_Summariser\app.py"
