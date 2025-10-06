@echo off
REM LALO AI Server Startup Script
REM This starts the server and keeps it running in the foreground

echo ============================================================
echo LALO AI Server - Starting...
echo ============================================================
echo.
echo The server will start and display "Uvicorn running on..."
echo This means it's WORKING and waiting for requests.
echo.
echo To test: Open a browser to http://127.0.0.1:8000
echo To stop: Press Ctrl+C
echo.
echo ============================================================
echo.

python -m uvicorn app:app --host 127.0.0.1 --port 8000 --log-level info

echo.
echo Server stopped.
pause
