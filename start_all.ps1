# PowerShell script to clean up ports, start services, and automate devops tasks
# Usage: Run in workspace root as administrator for process kill
# Args: -Backend, -Frontend, -Docker, -Test, -Build, -All (default: all)

# ---CONFIG ---
$backendPort = 8000
$frontendPort = 3000
$frontendDir = "lalo-frontend"
$backendEntry = "app:app"
$backendLogLevel = "debug"
$backendHealthUrl = "http://localhost:$backendPort/docs"
$frontendHealthUrl = "http://localhost:$frontendPort"
$envFile = ".env"
$logDir = "logs"
$pythonMinVersion = "3.10"
$nodeMinVersion = "16.0.0"
$dockerMinVersion = "20.10.0"

# --- FUNCTIONS ---

function Kill-PortProcess($port) {
    Write-Host "Checking port $port..."
    $proc = netstat -ano | findstr ":$port"
    if ($proc) {
        $lines = $proc -split "\n"
        foreach ($line in $lines) {
            if ($line -match "LISTENING") {
                $procId = ($line -split '\s+')[-1]
                if ($procId -match "^\d+$") {
                    Write-Host "  Killing process on port $port (PID: $procId)"
                    try {
                        taskkill /PID $procId /F 2>&1 | Out-Null
                    } catch {
                        Write-Warning "  Could not kill PID $procId"
                    }
                }
            }
        }
    } else {
        Write-Host "  No process found on port $port"
    }
}

function Validate-Env {
    Write-Host "`nValidating environment..."
    if (!(Test-Path $envFile)) {
        Write-Warning ".env file not found! Creating from template..."
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" $envFile
        }
    } else {
        $envVars = Get-Content $envFile | Where-Object {$_ -match "^[A-Za-z0-9_]+="}
        Write-Host "  Found $($envVars.Count) environment variables"
    }
}

function Clean-Logs {
    Write-Host "`nCleaning old logs..."
    if (Test-Path $logDir) {
        Get-ChildItem $logDir -File | Remove-Item -Force
        Write-Host "  Logs cleared"
    } else {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Write-Host "  Log directory created"
    }
}

function Run-Alembic {
    Write-Host "`nRunning database migrations..."
    if (Test-Path "alembic.ini") {
        try {
            python -m alembic upgrade head
            Write-Host "  Migrations complete"
        } catch {
            Write-Warning "  Alembic migration failed: $_"
        }
    } else {
        Write-Host "  alembic.ini not found, skipping"
    }
}

function Check-Version($cmd, $minVersion, $name) {
    try {
        $output = & $cmd 2>&1 | Out-String
        $verNum = ($output -replace '[^0-9.]', '').Trim()
        Write-Host "  $name version: $verNum"
    } catch {
        Write-Warning "  Could not check $name version"
    }
}

function Install-PythonDependencies {
    Write-Host "`nChecking Python dependencies..."
    if (Test-Path "requirements.txt") {
        $installed = & python -m pip list --disable-pip-version-check 2>$null | Out-String
        if ($installed -match "fastapi" -and $installed -match "uvicorn") {
            Write-Host "  Core packages detected, skipping install"
            return
        }
        Write-Host "  Installing requirements (this may take a while)..."
        python -m pip install --upgrade pip --quiet
        python -m pip install -r requirements.txt --quiet
        Write-Host "  Dependencies installed"
    }
}

function Install-NodeDependencies {
    Write-Host "`nChecking Node dependencies..."
    if (Test-Path "$frontendDir\package.json") {
        Push-Location $frontendDir
        if (!(Test-Path "node_modules")) {
            Write-Host "  Installing npm packages..."
            npm install --silent
        } else {
            Write-Host "  node_modules exists, skipping install"
        }
        Pop-Location
    }
}

function Build-Frontend {
    Write-Host "`nBuilding frontend..."
    if (Test-Path "$frontendDir\package.json") {
        Push-Location $frontendDir
        npm run build
        Pop-Location
        Write-Host "  Build complete"
    }
}

function Run-BackendTests {
    Write-Host "`nRunning backend tests..."
    if (Test-Path "tests") {
        python -m pytest -q --tb=short
    }
}

function Run-FrontendTests {
    Write-Host "`nRunning frontend tests..."
    if (Test-Path "$frontendDir\package.json") {
        Push-Location $frontendDir
        $env:CI = "true"
        npm test -- --watchAll=false --passWithNoTests 2>&1 | Out-Null
        Pop-Location
        Write-Host "  Frontend tests complete"
    }
}

function Test-Health($url, $name, $retries=3) {
    for ($i=1; $i -le $retries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 2>&1
            if ($response.StatusCode -eq 200) {
                Write-Host "  $name is healthy at $url" -ForegroundColor Green
                return $true
            }
        } catch {
            if ($i -lt $retries) {
                Write-Host "  $name not ready (attempt $i/$retries), waiting..." -ForegroundColor Yellow
                Start-Sleep -Seconds 3
            }
        }
    }
    Write-Host "  $name health check failed" -ForegroundColor Red
    return $false
}

# --- ARGUMENT PARSING ---
$argsList = $args | ForEach-Object { $_.ToLower() }
$runBackend = $argsList -contains "-backend" -or $argsList -contains "-all" -or $argsList.Count -eq 0
$runFrontend = $argsList -contains "-frontend" -or $argsList -contains "-all" -or $argsList.Count -eq 0
$runDocker = $argsList -contains "-docker" -or $argsList -contains "-all"
$runDockerBuild = $argsList -contains "-dockerbuild"
$runTests = $argsList -contains "-test"
$runBuild = $argsList -contains "-build"

# --- BANNER ---
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LALO AI Platform - Startup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# --- VERSION CHECKS ---
Write-Host "`nChecking system requirements..."
Check-Version { python --version } $pythonMinVersion "Python"
Check-Version { node --version } $nodeMinVersion "Node"

# --- ENV VALIDATION ---
Validate-Env

# --- LOG CLEANUP ---
Clean-Logs

# --- CLEANUP PORTS ---
Write-Host "`nCleaning up existing processes..."
Kill-PortProcess $backendPort
Kill-PortProcess $frontendPort

# --- DOCKER ---
if ($runDocker) {
    Write-Host "`nManaging Docker services..."
    if (Test-Path "docker-compose.yml") {
        docker-compose down --remove-orphans 2>&1 | Out-Null
        if ($runDockerBuild) {
            Write-Host "  Building Docker images..."
            docker-compose build
        }
        docker-compose up -d
        Write-Host "  Docker services started"
    } else {
        Write-Host "  docker-compose.yml not found, skipping Docker"
    }
}

# --- INSTALL DEPENDENCIES ---
if (!$runTests) {
    Install-PythonDependencies
    Install-NodeDependencies
}

# --- DATABASE MIGRATIONS ---
Run-Alembic

# --- FRONTEND BUILD ---
if ($runBuild) {
    Build-Frontend
}

# --- START BACKEND ---
if ($runBackend) {
    Write-Host "`nStarting backend server..."
    $backendCmd = "cd '$PWD'; `$env:PYTHONIOENCODING='utf-8'; python -m uvicorn $backendEntry --port $backendPort --log-level $backendLogLevel"
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"$backendCmd`"" -WindowStyle Minimized
    Write-Host "  Backend starting on port $backendPort"
}

# --- START FRONTEND ---
if ($runFrontend) {
    Write-Host "`nStarting frontend server..."
    $frontendCmd = "cd '$PWD\$frontendDir'; npm start"
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"$frontendCmd`"" -WindowStyle Minimized
    Write-Host "  Frontend starting on port $frontendPort"
}

# --- WAIT FOR SERVICES ---
if ($runBackend -or $runFrontend) {
    Write-Host "`nWaiting for services to initialize..."
    Start-Sleep -Seconds 10
}

# --- HEALTH CHECKS ---
if ($runBackend -or $runFrontend) {
    Write-Host "`nPerforming health checks..."
    $backendHealthy = if ($runBackend) { Test-Health $backendHealthUrl "Backend" 5 } else { $true }
    $frontendHealthy = if ($runFrontend) { Test-Health $frontendHealthUrl "Frontend" 5 } else { $true }

    Write-Host ""
    if ($backendHealthy -and $frontendHealthy) {
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  ALL SERVICES ARE HEALTHY!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "`nAccess points:"
        if ($runBackend) { Write-Host "  Backend:  $backendHealthUrl" -ForegroundColor Cyan }
        if ($runFrontend) { Write-Host "  Frontend: $frontendHealthUrl" -ForegroundColor Cyan }
    } else {
        Write-Host "========================================" -ForegroundColor Yellow
        Write-Host "  STARTUP COMPLETE (WITH WARNINGS)" -ForegroundColor Yellow
        Write-Host "========================================" -ForegroundColor Yellow
        Write-Host "`nSome services may not be ready yet."
        Write-Host "Check the individual service windows for details."
    }
}

# --- TEST RUNS ---
if ($runTests) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  RUNNING TESTS" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Run-BackendTests
    Run-FrontendTests
}

Write-Host ""
