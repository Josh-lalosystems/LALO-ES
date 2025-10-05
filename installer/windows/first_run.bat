@echo off
REM Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
REM
REM PROPRIETARY AND CONFIDENTIAL
REM
REM LALO AI Platform - First Run Setup Script

title LALO AI - First Run Setup

set "LALO_DIR=%~dp0"
cd /d "%LALO_DIR%"

echo ========================================
echo   LALO AI Platform - First Run Setup
echo ========================================
echo.

REM Check Python exists
if not exist "python\python.exe" (
    echo ERROR: Python embeddable not found!
    echo Expected location: %LALO_DIR%python\python.exe
    pause
    exit /b 1
)

set "PYTHON=%LALO_DIR%python\python.exe"

echo [1/5] Checking Python version...
"%PYTHON%" --version
if errorlevel 1 (
    echo ERROR: Python check failed!
    pause
    exit /b 1
)
echo.

echo [2/5] Installing pip (if needed)...
"%PYTHON%" -m ensurepip >nul 2>&1
"%PYTHON%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Installing get-pip.py...
    curl -o get-pip.py https://bootstrap.pypa.io/get-pip.py
    "%PYTHON%" get-pip.py
    del get-pip.py
)
echo.

echo [3/5] Installing Python dependencies...
echo This may take several minutes...
"%PYTHON%" -m pip install -r requirements.txt --no-warn-script-location
if errorlevel 1 (
    echo ERROR: Dependency installation failed!
    pause
    exit /b 1
)
echo.

echo [4/5] Initializing database...
if not exist "data" mkdir data
"%PYTHON%" scripts\init_db.py
if errorlevel 1 (
    echo WARNING: Database initialization had issues
    echo You may need to run this manually later
)
echo.

echo [5/5] Downloading AI models...
echo.
echo IMPORTANT: Model downloads will require approximately 20-25 GB of disk space.
echo.
set /p DOWNLOAD_MODELS="Download models now? (Y/N): "
if /i "%DOWNLOAD_MODELS%"=="Y" (
    echo.
    echo Downloading essential AI models (Priority 1)...
    echo This will take 15-30 minutes depending on your internet connection.
    echo.
    "%PYTHON%" scripts\download_all_production_models.py --priority 1 --auto-confirm
    if errorlevel 1 (
        echo WARNING: Model download had issues
        echo You can download models later by running:
        echo   python scripts\download_all_production_models.py
    )
) else (
    echo.
    echo Skipping model download.
    echo You can download models later by running:
    echo   python scripts\download_all_production_models.py
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo You can now start LALO AI Platform by running start.bat
echo or using the desktop shortcut.
echo.
pause
