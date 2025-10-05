@echo off
REM Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
REM
REM PROPRIETARY AND CONFIDENTIAL
REM
REM LALO AI Platform - Windows Startup Script

title LALO AI Platform

REM Get the directory where this batch file is located
set "LALO_DIR=%~dp0"
cd /d "%LALO_DIR%"

REM Check if Python embeddable exists
if not exist "python\python.exe" (
    echo ERROR: Python not found!
    echo Please reinstall LALO AI Platform.
    pause
    exit /b 1
)

REM Check if dependencies are installed
if not exist "python\Lib\site-packages\fastapi" (
    echo First time setup detected...
    echo Running dependency installation...
    call first_run.bat
    if errorlevel 1 (
        echo Setup failed!
        pause
        exit /b 1
    )
)

REM Set Python path
set "PYTHON=%LALO_DIR%python\python.exe"
set "PYTHONPATH=%LALO_DIR%;%PYTHONPATH%"

REM Check for .env file
if not exist ".env" (
    echo Creating .env from template...
    copy .env.example .env >nul
    echo Please edit .env file with your configuration.
    echo Opening .env in notepad...
    start notepad .env
    pause
)

REM Start the backend server
echo ========================================
echo   LALO AI Platform - Starting Server
echo ========================================
echo.
echo Server will start on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

"%PYTHON%" app.py

REM If server exits, show message
echo.
echo Server stopped.
pause
