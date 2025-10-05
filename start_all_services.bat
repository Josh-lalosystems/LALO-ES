# Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of LALO AI Platform and is protected by copyright law.
# Unauthorized copying, modification, distribution, or use of this software,
# via any medium, is strictly prohibited without the express written permission
# of LALO AI SYSTEMS, LLC.
#

@echo off
echo ============================================================
echo LALO AI - Starting All Services
echo ============================================================
echo.

REM Check if we're in the right directory
if not exist "app.py" (
    echo Error: Please run this script from the LALOai-main directory
    pause
    exit /b 1
)

echo [1/5] Building Frontend...
cd lalo-frontend
call npm run build
if errorlevel 1 (
    echo Frontend build failed!
    pause
    exit /b 1
)
cd ..
echo [OK] Frontend built successfully
echo.

echo [2/5] Starting Main LALO Application (Port 8000)...
start "LALO Main App" cmd /k "python app.py"
timeout /t 3 /nobreak > nul
echo [OK] Main app starting...
echo.

echo [3/5] Starting RTI Service (Port 8101)...
cd rtinterpreter
start "RTI Service" cmd /k "python -m uvicorn main:app --port 8101"
cd ..
timeout /t 2 /nobreak > nul
echo [OK] RTI service starting...
echo.

echo [4/5] Starting MCP Service (Port 8102)...
cd mcp
start "MCP Service" cmd /k "python -m uvicorn main:app --port 8102"
cd ..
timeout /t 2 /nobreak > nul
echo [OK] MCP service starting...
echo.

echo [5/5] Starting Creation Service (Port 8103)...
cd creation
start "Creation Service" cmd /k "python -m uvicorn main:app --port 8103"
cd ..
timeout /t 2 /nobreak > nul
echo [OK] Creation service starting...
echo.

echo ============================================================
echo ALL SERVICES STARTED
echo ============================================================
echo.
echo Services running:
echo   - Main App:     http://localhost:8000
echo   - RTI Service:  http://localhost:8101
echo   - MCP Service:  http://localhost:8102
echo   - Creation:     http://localhost:8103
echo.
echo Frontend available at: http://localhost:8000/workflow
echo.
echo Press any key to open the application in your browser...
pause > nul

start http://localhost:8000/workflow

echo.
echo Services are running. Close terminal windows to stop services.
echo.
pause
