@echo off
REM LALO AI Server - Background Startup
REM This starts the server in the background so you can continue working

echo ============================================================
echo LALO AI Server - Starting in Background...
echo ============================================================
echo.

start /B python -m uvicorn app:app --host 127.0.0.1 --port 8000

timeout /t 5 /nobreak > nul

echo Testing server...
curl -s http://127.0.0.1:8000/ > nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Server is running on http://127.0.0.1:8000
    echo.
    echo To stop the server:
    echo   1. Open Task Manager
    echo   2. Find "Python" process
    echo   3. End task
    echo.
    echo Or run: taskkill /F /IM python.exe
) else (
    echo [FAIL] Server may not have started correctly
    echo Check for errors above
)

echo.
pause
