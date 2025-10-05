<#
PowerShell helper: download and extract the Python 3.11 embeddable package for the installer.
Usage: Run this from the repository root or from the installer\windows folder.
    cd installer\windows
    .\get_python_embeddable.ps1 -OutDir "python-3.11.9-embed-amd64" -Quiet
#>
param(
    [string]$Version = "3.11.9",
    [string]$Arch = "amd64",
    [string]$OutDir = "python-3.11.9-embed-amd64",
    [switch]$Quiet
)

$baseUrl = "https://www.python.org/ftp/python"
$zipName = "python-$Version-embed-$Arch.zip"
$url = "$baseUrl/$Version/$zipName"
$destZip = Join-Path -Path (Get-Location) -ChildPath $zipName

if (-Not $Quiet) { Write-Host "Downloading $url -> $destZip" }

try {
    Invoke-WebRequest -Uri $url -OutFile $destZip -UseBasicParsing -ErrorAction Stop
} catch {
    Write-Error "Failed to download $url: $_"
    exit 1
}

if (-Not $Quiet) { Write-Host "Extracting to $OutDir" }

if (Test-Path $OutDir) {
    if (-Not $Quiet) { Write-Host "Removing existing $OutDir" }
    Remove-Item -Recurse -Force $OutDir
}

try {
    Expand-Archive -Path $destZip -DestinationPath $OutDir -Force
} catch {
    Write-Error "Failed to extract $destZip: $_"
    exit 2
}

# Prepare the embeddable to support pip by creating the _pth file with import site enabled
$pthFile = Join-Path -Path $OutDir -ChildPath "python311._pth"
$pthContent = @"
python311.zip
.

# Uncomment to run site.main() automatically
import site
"@

if (-Not $Quiet) { Write-Host "Writing $pthFile" }
Set-Content -Path $pthFile -Value $pthContent -Encoding UTF8

# Cleanup zip
if (-Not $Quiet) { Write-Host "Cleaning up $destZip" }
Remove-Item -Force $destZip

if (-Not $Quiet) { Write-Host "Python embeddable prepared in: $OutDir" }

Exit 0
