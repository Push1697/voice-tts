@echo off
title VaniForge TTS Studio
setlocal enabledelayedexpansion

echo =======================================================
echo          VaniForge Neural Speech Studio (TTS)
echo    Hardware Accelerated - Hindi & English Synthesis
echo =======================================================
echo.

:: Ensure current working directory is script directory
cd /d "%~dp0"

:: Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

:: Check for virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Setting up Python virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [2/3] Installing dependencies...
    .\.venv\Scripts\pip install -r requirements.txt
)

:: Pre-flight check complete
echo [3/3] Launching VaniForge Studio Server...
echo.
echo Application will be available at: http://127.0.0.1:8000
echo.

:: Automatically open default web browser after 2 seconds in background
start "" /b cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000"

:: Start Uvicorn Server
.\.venv\Scripts\python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000

pause
