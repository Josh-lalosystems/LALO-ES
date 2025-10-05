"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

<#
Create a standalone bundle that contains the repository, offline pip wheels, npm cache, and optional installers.

This script will:
- Create a zip of the repository (excluding node_modules and venv)
- Include the offline_bundle contents if present
- Optionally include system installers (VS Build Tools, CMake, Docker) if provided in an 'external_installers' folder
- Produce a single ZIP in ./dist/ that can be distributed.

To make a true single-executable installer on Windows, you can wrap the produced ZIP with an NSIS or 7-Zip SFX; this script produces the ZIP only.
#>

Set-StrictMode -Version Latest
$RepoRoot = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $RepoRoot

function Write-Log($m) { "$((Get-Date).ToString('s')) $m" | Tee-Object -FilePath "$RepoRoot\dist\bundle_build.log" -Append }

$dist = Join-Path $RepoRoot 'dist'
if (-not (Test-Path $dist)) { New-Item -ItemType Directory -Path $dist | Out-Null }

$tmp = Join-Path $dist 'bundle_temp'
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
New-Item -ItemType Directory -Path $tmp | Out-Null

Write-Log "Copying repository (excluding venv/node_modules)..."
Get-ChildItem -Path $RepoRoot -Force | Where-Object {
  $_.Name -notin @('venv','node_modules','dist','offline_bundle','build','.git')
} | ForEach-Object {
  $dest = Join-Path $tmp $_.Name
  if ($_.PSIsContainer) { Copy-Item $_.FullName -Destination $dest -Recurse -Force -ErrorAction SilentlyContinue } else { Copy-Item $_.FullName -Destination $dest -Force }
}

if (Test-Path (Join-Path $RepoRoot 'offline_bundle')) {
  Write-Log "Including offline_bundle"
  Copy-Item -Path (Join-Path $RepoRoot 'offline_bundle') -Destination $tmp -Recurse -Force
}

if (Test-Path (Join-Path $RepoRoot 'external_installers')) {
  Write-Log "Including external installers"
  Copy-Item -Path (Join-Path $RepoRoot 'external_installers') -Destination $tmp -Recurse -Force
}

$outZip = Join-Path $dist "lalo_standalone_bundle_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
Write-Log "Creating zip bundle at $outZip"
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($tmp, $outZip)

Write-Log "Bundle created: $outZip"
Write-Log "To create an SFX .exe, use 7-Zip's SFX or an NSIS script to wrap this zip with extraction and run logic."
