"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

<#
Comprehensive Windows installer for the LALOai project.

This script performs common setup tasks for a Windows dev environment:
- Check for admin privileges
- Detect winget or Chocolatey
- Create / activate a Python virtual environment and install requirements
- Optionally install heavy ML requirements from requirements-ml.txt
- Install Node dependencies (npm install) and build frontend
- Offer to install Visual Studio Build Tools, CMake, Docker Desktop via winget

Usage (run from repo root):
  .\installer_windows.ps1 -All
  .\installer_windows.ps1 -Python -Node -Frontend -ML

Run with -WhatIf to preview actions.
#>

param(
  [switch]$All,
  [switch]$Python,
  [switch]$Node,
  [switch]$Frontend,
  [switch]$Docker,
  [switch]$VSBuildTools,
  [switch]$CMake,
  [switch]$ML,
  [switch]$Auto,
  [string]$OfflineBundlePath,
  [switch]$WhatIf
)

Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $RepoRoot

function Write-Log($msg) {
  $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  "$ts  $msg" | Tee-Object -FilePath "$RepoRoot\installer_logs.txt" -Append
  Write-Host $msg
}

function Ensure-Admin {
  $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not $isAdmin) {
    Write-Host "This script prefers running as Administrator for system installs. You can continue but some steps will require elevation." -ForegroundColor Yellow
  }
}

function Has-Command($name) {
  return (Get-Command $name -ErrorAction SilentlyContinue) -ne $null
}

function Detect-PackageManager {
  if (Has-Command winget) { return 'winget' }
  if (Has-Command choco) { return 'choco' }
  return $null
}

function Winget-Install($id, $name) {
  if ($WhatIf) { Write-Host "WhatIf: winget install $id ($name)"; return }
  try {
    Write-Log "Installing $name via winget ($id)..."
    winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements
  } catch {
    Write-Log "winget install failed for $name: $_"
  }
}

function Create-Venv-And-Install-Python {
  Write-Log "Setting up Python virtual environment..."
  if (-not (Has-Command python)) { Write-Log "Python not found on PATH."; return }

  $venvPath = Join-Path $RepoRoot 'venv'
  if (-not (Test-Path $venvPath)) {
    if ($WhatIf) { Write-Host "WhatIf: python -m venv $venvPath"; } else { python -m venv $venvPath }
    Write-Log "Created venv at $venvPath"
  } else {
    Write-Log "Virtual environment already exists at $venvPath"
  }

  # Activate virtualenv in current shell for the remainder of the script
  $activate = Join-Path $venvPath 'Scripts\Activate.ps1'
  if (Test-Path $activate) {
    if (-not $WhatIf) { & $activate }
    Write-Log "Activated virtualenv"
  }

  # Upgrade pip and install core requirements. Support offline bundle if provided.
  if ($OfflineBundlePath -and (Test-Path $OfflineBundlePath)) {
    $wheelDir = Join-Path $OfflineBundlePath 'pip_wheels'
    if (Test-Path $wheelDir) {
      Write-Log "Installing Python packages from offline bundle: $wheelDir"
      if (-not $WhatIf) { python -m pip install --no-index --find-links "$wheelDir" -r requirements.txt }
    } else {
      Write-Log "Offline bundle does not contain pip_wheels, falling back to online install"
    }
  }

  if (Test-Path "$RepoRoot\requirements.txt" -and -not $OfflineBundlePath) {
    Write-Log "Upgrading pip and installing requirements.txt..."
    if (-not $WhatIf) { python -m pip install --upgrade pip }
    if (-not $WhatIf) { python -m pip install -r requirements.txt }
  } elseif (-not (Test-Path "$RepoRoot\requirements.txt")) {
    Write-Log "requirements.txt not found, skipping pip install"
  }

  if ($ML) {
    if ($OfflineBundlePath -and (Test-Path $OfflineBundlePath)) {
      $mlWheelDir = Join-Path $OfflineBundlePath 'pip_wheels_ml'
      if (Test-Path $mlWheelDir) {
        Write-Log "Installing ML packages from offline bundle: $mlWheelDir"
        if (-not $WhatIf) { python -m pip install --no-index --find-links "$mlWheelDir" -r requirements-ml.txt }
      } else {
        Write-Log "Offline bundle does not contain pip_wheels_ml, attempting online install"
        if (Test-Path "$RepoRoot\requirements-ml.txt" -and -not $WhatIf) { python -m pip install -r requirements-ml.txt }
      }
    } else {
      if (Test-Path "$RepoRoot\requirements-ml.txt") {
        Write-Log "Installing ML requirements (this may require Visual Studio Build Tools/CMake)..."
        if (-not $WhatIf) { python -m pip install -r requirements-ml.txt }
      }
    }
  }
}

function Install-Node-And-Frontend {
  Write-Log "Checking Node.js and frontend dependencies..."
  if (-not (Has-Command node)) { Write-Log "Node.js not found on PATH."; return }
  if (-not (Has-Command npm)) { Write-Log "npm not found on PATH."; return }

  $frontendDir = Join-Path $RepoRoot 'lalo-frontend'
  if (Test-Path $frontendDir) {
    Push-Location $frontendDir
    if (-not (Test-Path 'node_modules')) {
      if ($WhatIf) { Write-Host "WhatIf: npm install" } else { npm install }
      Write-Log "npm install completed"
    } else { Write-Log "node_modules exists, skipping npm install" }

    if ($Frontend) {
      if ($WhatIf) { Write-Host "WhatIf: npm run build" } else { npm run build }
      Write-Log "Frontend build complete"
    }
    Pop-Location
  } else {
    Write-Log "Frontend directory not found: $frontendDir"
  }
}

function Install-Optional-Tools($pm) {
  if ($pm -eq 'winget') {
    Write-Log "Using winget to install optional tools (Visual Studio Build Tools, CMake, Docker)..."
    if ($VSBuildTools) { Winget-Install 'Microsoft.VisualStudio.2022.BuildTools' 'Visual Studio 2022 Build Tools' }
    if ($CMake) { Winget-Install 'Kitware.CMake' 'CMake' }
    if ($Docker) { Winget-Install 'Docker.DockerDesktop' 'Docker Desktop' }
  } elseif ($pm -eq 'choco') {
    Write-Log "Using Chocolatey to install optional tools (requires admin)."
    if ($VSBuildTools) { choco install visualstudio2022buildtools -y }
    if ($CMake) { choco install cmake -y }
    if ($Docker) { choco install docker-desktop -y }
  } else {
    Write-Log "No package manager detected for optional tool installs. Use winget or Chocolatey to automate these steps."
    Write-Log "Manual install links: Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/ (Build Tools), CMake: https://cmake.org/download/, Docker Desktop: https://www.docker.com/get-started"
  }
}

### Main
Ensure-Admin

$pm = Detect-PackageManager
if ($All) { $Python = $true; $Node = $true; $Frontend = $true; $Docker = $true; $VSBuildTools = $true; $CMake = $true }

if ($Python) { Create-Venv-And-Install-Python }
if ($Node) { Install-Node-And-Frontend }

if ($VSBuildTools -or $CMake -or $Docker) { Install-Optional-Tools $pm }

Write-Log "Installer run complete. Review installer_logs.txt for details."
