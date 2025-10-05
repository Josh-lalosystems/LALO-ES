@echo off
REM Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
REM
REM PROPRIETARY AND CONFIDENTIAL
REM
REM LALO AI Platform - Dependency Installation Script

title LALO AI - Installing Dependencies

set "LALO_DIR=%~dp0"
cd /d "%LALO_DIR%"
set "PYTHON=%LALO_DIR%python\python.exe"

echo ========================================
echo   Installing Dependencies
echo ========================================
echo.

"%PYTHON%" -m pip install -r requirements.txt --no-warn-script-location

if errorlevel 1 (
    echo.
    echo ERROR: Installation failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
pause
