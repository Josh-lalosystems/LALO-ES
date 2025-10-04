<#
Create offline bundle containing pip wheels and npm tarballs for offline installation.

This script will:
- Create ./offline_bundle/pip_wheels and pip_wheels_ml
- Download wheels for packages listed in requirements.txt and requirements-ml.txt using pip wheel
- Create ./offline_bundle/npm_cache with npm pack tarballs for dependencies listed in lalo-frontend/package.json

Usage:
  .\create_offline_bundle.ps1
#>

Set-StrictMode -Version Latest
$RepoRoot = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $RepoRoot

function Write-Log($m) { "$((Get-Date).ToString('s')) $m" | Tee-Object -FilePath "$RepoRoot\offline_bundle\bundle_build.log" -Append }

if (-not (Get-Command pip -ErrorAction SilentlyContinue)) { Write-Host "pip not found on PATH"; exit 1 }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Write-Host "npm not found on PATH"; exit 1 }

$bundleDir = Join-Path $RepoRoot 'offline_bundle'
if (-not (Test-Path $bundleDir)) { New-Item -ItemType Directory -Path $bundleDir | Out-Null }

$wheelDir = Join-Path $bundleDir 'pip_wheels'
$wheelDirML = Join-Path $bundleDir 'pip_wheels_ml'
if (-not (Test-Path $wheelDir)) { New-Item -ItemType Directory -Path $wheelDir | Out-Null }
if (-not (Test-Path $wheelDirML)) { New-Item -ItemType Directory -Path $wheelDirML | Out-Null }

if (Test-Path 'requirements.txt') {
  Write-Log "Building wheels for requirements.txt"
  python -m pip wheel -r requirements.txt -w $wheelDir
} else { Write-Log "requirements.txt missing, skipping" }

if (Test-Path 'requirements-ml.txt') {
  Write-Log "Building wheels for requirements-ml.txt"
  python -m pip wheel -r requirements-ml.txt -w $wheelDirML
} else { Write-Log "requirements-ml.txt missing, skipping" }

# NPM packages: create a cache of tarballs via npm pack
$npmCache = Join-Path $bundleDir 'npm_cache'
if (-not (Test-Path $npmCache)) { New-Item -ItemType Directory -Path $npmCache | Out-Null }

$frontendDir = Join-Path $RepoRoot 'lalo-frontend'
if (Test-Path (Join-Path $frontendDir 'package.json')) {
  Push-Location $frontendDir
  $pkg = Get-Content package.json | ConvertFrom-Json
  $deps = @{}
  if ($pkg.dependencies) { $pkg.dependencies.PSObject.Properties | ForEach-Object { $deps[$_.Name] = $_.Value } }
  if ($pkg.devDependencies) { $pkg.devDependencies.PSObject.Properties | ForEach-Object { $deps[$_.Name] = $_.Value } }
  foreach ($d in $deps.GetEnumerator()) {
    try {
      Write-Log "Packing npm package $($d.Key)@$($d.Value)"
      npm pack "$($d.Key)@$($d.Value)" | ForEach-Object {
        Move-Item -Path $_ -Destination $npmCache -Force
      }
    } catch {
      Write-Log "npm pack failed for $($d.Key)@$($d.Value): $_"
    }
  }
  Pop-Location
} else {
  Write-Log "Frontend package.json missing, skipping npm cache creation"
}

Write-Log "Offline bundle prepared at $bundleDir"
