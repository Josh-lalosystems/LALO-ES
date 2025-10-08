# start_dev_detached.ps1
# Starts backend (uvicorn) and frontend (npm start) as detached processes and redirects logs to files.
# Usage: open PowerShell as Administrator (or normal) and run from repo root:
#   .\scripts\start_dev_detached.ps1

param(
    [string]$RepoRoot = "$PSScriptRoot\..",
    [int]$BackendPort = 8000,
    [switch]$EnableDemoMode
)

$repo = Resolve-Path -Path $RepoRoot
$repo = $repo.Path
Write-Output "Repo root: $repo"

# Ensure logs directory
$logDir = Join-Path $repo 'logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

# Backend command
$python = Join-Path $repo 'venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    Write-Output "ERROR: Python not found at $python. Activate venv or update path in script."; exit 1
}

$uvicornArgs = @('-m','uvicorn','app:app',"--host","0.0.0.0","--port",$BackendPort.ToString())
# Do not pass --reload by default here to avoid reloader scanning issues; add --reload if you want auto-reload
# To enable reload, uncomment the following two lines and adjust watched dirs if needed:
# $uvicornArgs += '--reload'
# $uvicornArgs += '--reload-dir'; $uvicornArgs += (Join-Path $repo 'core')

$backendOut = Join-Path $logDir 'backend.out.log'
$backendErr = Join-Path $logDir 'backend.err.log'

Write-Output "Starting backend detached (python) -> stdout: $backendOut, stderr: $backendErr"

# If demo mode is requested, set environment variable so the child process inherits it.
if ($EnableDemoMode) {
    Write-Output "Enabling DEMO_MODE for backend process (DEMO_MODE=true)"
    $env:DEMO_MODE = 'true'
} else {
    # Ensure we don't accidentally inherit host demo mode unless explicitly requested
    if ($env:DEMO_MODE) { Remove-Item Env:\DEMO_MODE -ErrorAction SilentlyContinue }
}

$backendProc = Start-Process -FilePath $python -ArgumentList $uvicornArgs -WorkingDirectory $repo -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -WindowStyle Hidden -PassThru
Write-Output "Backend PID: $($backendProc.Id)"

# Frontend command
$npm = 'npm'
$frontendDir = Join-Path $repo 'lalo-frontend'
$frontendOut = Join-Path $logDir 'frontend.out.log'
$frontendErr = Join-Path $logDir 'frontend.err.log'

if (-not (Test-Path $frontendDir)) { Write-Output "WARNING: frontend folder not found at $frontendDir" } else {
    Write-Output "Starting frontend detached (npm start) -> stdout: $frontendOut, stderr: $frontendErr"
    # On Windows, call cmd.exe /c npm start to ensure the npm shim (.cmd) is used and Start-Process can launch it.
    $npmCmd = "cmd.exe"
    $npmArgs = '/c npm start'
    try {
        $frontendProc = Start-Process -FilePath $npmCmd -ArgumentList $npmArgs -WorkingDirectory $frontendDir -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr -WindowStyle Hidden -PassThru
        Write-Output "Frontend PID: $($frontendProc.Id)"
    } catch {
        Write-Output "ERROR starting frontend: $($_.Exception.Message)"
        Write-Output "Attempting fallback: start in new window"
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c start npm start" -WorkingDirectory $frontendDir
    }
}

Write-Output "All processes started. Tail logs with:'Get-Content -Path $logDir\backend.out.log -Wait' and similarly for frontend.out.log"