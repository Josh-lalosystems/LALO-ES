# Windows Installer for LALOai

This repository includes a convenience installer script to help set up a development environment on Windows.

Files
- `installer_windows.ps1` - PowerShell installer that can create a virtualenv, install Python and Node deps, build the frontend, and optionally install system tools via winget/choco.

Usage
1. Open PowerShell as Administrator (recommended for system installs).
2. From the repo root run one of the following:

```powershell
# Full run (create venv, install Python & Node deps, build frontend, attempt optional tool installs)
.\installer_windows.ps1 -All

# Minimal: only Python venv + requirements
.\installer_windows.ps1 -Python

# Install Node deps and build frontend
.\installer_windows.ps1 -Node -Frontend

# Install ML dependencies (heavy; requires C/C++ toolchain)
.\installer_windows.ps1 -Python -ML
```

Options
- `-WhatIf` — preview actions without making changes.
- `-ML` — install `requirements-ml.txt` (contains heavy ML packages such as `torch` and `llama-cpp-python`). Only run on machines with the required toolchain or where wheels are available.
- `-VSBuildTools` / `-CMake` / `-Docker` — when combined with `-All` or specified, the script will attempt to install these via `winget` or `choco`.

Notes and recommendations
- The ML requirements are intentionally separated into `requirements-ml.txt`. Installing them on a laptop without the Visual Studio Build Tools or CMake will likely fail for packages like `llama-cpp-python`.
- For `llama-cpp-python` and other build-from-source packages on Windows, install:
  - Visual Studio 2022 Build Tools (Desktop development with C++)
  - CMake
  - (Optional) Windows SDK
- If you do not have `winget` or `choco`, the installer will not auto-install system tools; it will print manual install links.
- The script writes a simple log to `installer_logs.txt` in the repo root.

Security
- The script may call out to system installers (winget/choco) which require admin privileges. Inspect the script before running and use `-WhatIf` to preview.

Troubleshooting
- If pip install for ML packages fails with CMake or compiler errors, install Visual Studio Build Tools and CMake, then re-run with `-ML`.
- If Node/npm networking fails (SSL errors), re-run the network checks described in the main README or contact your network admin to whitelist `registry.npmjs.org` and `pypi.org`.

Want help running it?
- Tell me which flags to run (for example, `-Python -Node -Frontend`) and I'll execute the installer in the workspace and report back. I can also run network diagnostics first if you saw SSL errors earlier.

Offline & Standalone bundle creation
- `create_offline_bundle.ps1` — builds pip wheels for `requirements.txt` and `requirements-ml.txt` and creates npm tarballs (via `npm pack`) for frontend dependencies in `offline_bundle/`. Use this to prepare an offline cache for installs on air-gapped systems.
- `create_standalone_bundle.ps1` — packages the repository plus `offline_bundle` into a single ZIP in `dist/`. You can distribute this archive to another Windows machine and run the installer with `installer_windows.ps1 -OfflineBundlePath <path-to-extracted-offline_bundle>`.

Making a single-executable installer
1. Produce the ZIP using `create_standalone_bundle.ps1`.
2. On a machine with 7-Zip, you can create a self-extracting EXE with a small config that extracts the ZIP and runs `installer_windows.ps1` automatically. Example (manual steps):
  - Install 7-Zip and use `7z a -r bundle.7z dist\lalo_standalone_bundle_*.zip` to create a 7z archive.
  - Use the 7-Zip SFX module to build an EXE that extracts and runs `powershell.exe -ExecutionPolicy Bypass -File installer_windows.ps1 -OfflineBundlePath .\offline_bundle -Python -Node -Frontend`.
3. Alternatively, create an NSIS installer script (makes a polished installer with progress and uninstaller). NSIS can bundle the ZIP and run the included PowerShell script on first run.

Security & distribution notes
- The produced EXE (SFX) will execute a PowerShell script on extraction. Code-signing the EXE and the PowerShell scripts is strongly recommended before distributing to users.
- Large ML wheels (torch, triton) can make the bundle several GB. Ensure your distribution medium supports large files.

