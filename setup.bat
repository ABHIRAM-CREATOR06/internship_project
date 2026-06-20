@echo off
title BankPulse - Full Setup
echo ============================================
echo   BankPulse - Full Environment Setup
echo ============================================
echo.

:: Step 1 - Kill any running Python processes
echo [1/5] Stopping running Python processes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
taskkill /f /im jupyter.exe >nul 2>&1
taskkill /f /im jupyter-notebook.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo       Done.
echo.

:: Step 2 - Remove old venv if it exists
echo [2/5] Removing old virtual environment...
if exist venv (
    rmdir /s /q venv
    if exist venv (
        echo       ERROR: Could not delete venv folder.
        echo       Close all terminals, IDEs, and OneDrive, then try again.
        pause
        exit /b 1
    )
    echo       Old venv removed.
) else (
    echo       No existing venv found. Skipping.
)
echo.

:: Step 3 - Create new venv
echo [3/5] Creating new virtual environment...
python -m venv venv
if errorlevel 1 (
    echo       ERROR: Failed to create virtual environment.
    echo       Make sure Python is installed and on your PATH.
    pause
    exit /b 1
)
echo       Virtual environment created.
echo.

:: Step 4 - Activate venv and install dependencies
echo [4/5] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo       ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo       Dependencies installed.
echo.

:: Step 5 - Start the Flask server
echo [5/5] Starting BankPulse server...
echo ============================================
echo   Server running at http://127.0.0.1:5000
echo   Press Ctrl+C to stop
echo ============================================
echo.
python backend\app.py
pause
