@echo off
title AI Text Summarizer
cd /d "%~dp0"

echo ===================================================
echo   AI Text Summarizer - Quick Launcher
echo ===================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/2] Creating virtual environment...
    python -m venv .venv
    echo [2/2] Installing requirements...
    .\.venv\Scripts\pip install -r requirements.txt
)

echo [INFO] Starting AI Text Summarizer...
echo [INFO] Your browser will open automatically at http://127.0.0.1:5000
echo.
echo Press Ctrl+C in this window anytime to stop the server.
echo.

.\.venv\Scripts\python.exe Text_Summariser\app.py

if errorlevel 1 (
    echo.
    echo An error occurred while running the server.
    pause
)
