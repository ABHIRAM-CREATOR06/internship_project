@echo off
title BankPulse - Quick Start
echo ============================================
echo   BankPulse - Quick Start
echo ============================================
echo.

:: Step 1 - Kill any running Python processes (Flask, Jupyter, etc.)
echo [1/2] Stopping old Python processes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
timeout /t 1 /nobreak >nul
echo       Done.
echo.

:: Step 2 - Activate venv and start server
echo [2/2] Starting BankPulse server...
if not exist venv\Scripts\activate.bat (
    echo       ERROR: Virtual environment not found.
    echo       Run setup.bat first to create it.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
echo.
echo ============================================
echo   Server running at http://127.0.0.1:5000
echo   Press Ctrl+C to stop
echo ============================================
echo.
python backend\app.py
pause
