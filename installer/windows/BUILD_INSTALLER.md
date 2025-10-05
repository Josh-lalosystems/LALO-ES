# Windows Installer Build Guide

Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

## Overview

This guide explains how to build the LALO AI Platform Windows installer using Inno Setup.

## Prerequisites

### Required Software

1. **Inno Setup 6.x**
   - Download: https://jrsoftware.org/isdl.php
   - Install the full version (includes compiler)
   - Version 6.2.0 or newer recommended

2. **Python 3.11 Embeddable Package**
   - Download: https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip
   - Extract to: `installer/windows/python-3.11.9-embed-amd64/`

3. **Built Frontend**
   - Already built if you ran: `cd lalo-frontend && npm run build`
   - Output in: `lalo-frontend/build/`

### File Checklist

Before building, ensure these files exist:

```
LALOai-main/
├── installer/
│   └── windows/
│       ├── lalo-ai-setup.iss           ✓ Inno Setup script
│       ├── start.bat                   ✓ Startup script
│       ├── first_run.bat              ✓ First run setup
│       ├── install_deps.bat           ✓ Dependency installer
│       ├── .env.example               ✓ Configuration template
│       ├── readme-before-install.txt  ✓ Pre-install info
│       ├── readme-after-install.txt   ✓ Post-install info
│       ├── lalo-icon.ico              ⚠️ TODO: Add icon
│       └── python-3.11.9-embed-amd64/ ⚠️ Download required
│           ├── python.exe
│           ├── python311.dll
│           └── ...
├── lalo-frontend/
│   └── build/                         ✓ Frontend build
│       ├── index.html
│       └── static/
├── core/                              ✓ Backend code
├── app.py                             ✓ Main application
├── requirements.txt                   ✓ Dependencies
├── LICENSE                            ✓ License file
└── README.md                          ✓ Documentation
```

## Build Steps

### Step 1: Download Python Embeddable

```powershell
# Navigate to installer directory
cd installer\windows

# Download Python 3.11 embeddable (64-bit)
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip" -OutFile "python-embed.zip"

# Extract
Expand-Archive -Path "python-embed.zip" -DestinationPath "python-3.11.9-embed-amd64"

# Cleanup
Remove-Item "python-embed.zip"
```

Or manually:
1. Download from: https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip
2. Extract to: `installer/windows/python-3.11.9-embed-amd64/`

Alternatively, a small helper script is included to automate this step:

```powershell
# From repository root:
cd installer\windows
.\get_python_embeddable.ps1 -OutDir "python-3.11.9-embed-amd64"
```

This script downloads the embeddable zip, extracts it to the target folder, writes a `python311._pth` that enables `site` so pip can be used, and removes the temporary zip.

### Step 2: Prepare Python Embeddable for pip

The embeddable Python doesn't include pip by default. We need to enable it:

```powershell
cd python-3.11.9-embed-amd64

# Create a ._pth file to enable site-packages
# This allows pip to install packages
$pythonPath = "python311._pth"
$content = @"
python311.zip
.

# Uncomment to run site.main() automatically
import site
"@
Set-Content -Path $pythonPath -Value $content
```

Or manually edit `python311._pth` and uncomment the last line (`import site`).

### Step 3: Build Frontend (if not already done)

```powershell
# From LALOai-main root
cd lalo-frontend
npm install
npm run build
```

Verify build output exists in `lalo-frontend/build/`

### Step 4: Create Application Icon (TODO)

You need to create or obtain a `lalo-icon.ico` file:

```powershell
# Placeholder - create a simple icon or use an existing one
# Place it in: installer\windows\lalo-icon.ico
```

**Icon Requirements:**
- Format: .ICO
- Sizes: 16x16, 32x32, 48x48, 256x256
- Recommended: Transparent background

**Temporary Workaround:**
If no icon is available, comment out these lines in `lalo-ai-setup.iss`:
```ini
; SetupIconFile=lalo-icon.ico
```

And these icon references:
```ini
; IconFilename: "{app}\lalo-icon.ico"
```

### Step 5: Build Installer with Inno Setup

#### Option A: GUI Method

1. Open Inno Setup Compiler
2. File → Open → Select `lalo-ai-setup.iss`
3. Build → Compile
4. Wait for compilation to complete
5. Output will be in: `dist/LALO-AI-Setup-1.0.0.exe`

#### Option B: Command Line Method

```powershell
# Navigate to LALOai-main root
cd c:\IT\LALOai-main

# Compile with Inno Setup command line compiler
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\windows\lalo-ai-setup.iss
```

### Step 6: Verify Installer

Check that the installer was created:

```powershell
dir dist\LALO-AI-Setup-1.0.0.exe
```

Expected size: ~500 MB (without models)

## Testing the Installer

### Test on Development Machine

1. **Backup current installation** (if any)
2. **Run the installer:**
   ```powershell
   dist\LALO-AI-Setup-1.0.0.exe
   ```
3. **Follow installation wizard**
4. **Choose installation directory** (default: C:\Program Files\LALO AI)
5. **Opt to run first_run.bat** after installation
6. **Test that application starts** and opens browser to localhost:8000

### Test on Clean Windows 11 Machine

**IMPORTANT:** This is the final test before distribution.

1. **Prepare test machine:**
   - Fresh Windows 11 installation or VM
   - No Python installed
   - No development tools

2. **Copy installer to test machine**

3. **Run installer as Administrator**

4. **Verify installation:**
   - Desktop shortcut created
   - Start menu entry created
   - Application launches successfully
   - Browser opens to login page
   - Models download (if selected)

5. **Test core functionality:**
   - Login with demo token
   - Add API keys
   - Send test request
   - Verify local model inference works

## Customization

### Change Version Number

Edit `lalo-ai-setup.iss`:

```ini
#define MyAppVersion "1.0.0"  ; Change this
```

Also update in `OutputBaseFilename`:

```ini
OutputBaseFilename=LALO-AI-Setup-1.0.0  ; Match version
```

### Change Installation Directory

Edit `lalo-ai-setup.iss`:

```ini
DefaultDirName={autopf}\LALO AI  ; Change "LALO AI"
```

### Disable Model Download Prompt

Edit `first_run.bat` and remove the user prompt, or set:

```batch
set DOWNLOAD_MODELS=N  ; Skip by default
```

### Include Models in Installer

**WARNING:** This will make the installer 20+ GB!

Edit `lalo-ai-setup.iss`:

```ini
[Files]
; Add this line:
Source: "..\..\models\*"; DestDir: "{app}\models"; Flags: ignoreversion recursesubdirs createallsubdirs
```

## Troubleshooting

### "Python not found" during build

- Ensure `python-3.11.9-embed-amd64/` exists in `installer/windows/`
- Verify `python.exe` is in that directory

### "File not found: lalo-icon.ico"

- Create an icon file or comment out icon references in the .iss file

### Installer size is too large (>1 GB)

- Make sure models/ directory is NOT included
- Check that `[Files]` section doesn't include unnecessary large files

### "Setup failed" when running installer

- Run installer as Administrator
- Check Windows Event Viewer for errors
- Verify disk space (500 MB + 25 GB for models)

### First run fails on test machine

- Check that internet connection is available (for pip packages)
- Verify `requirements.txt` is up to date
- Check logs in: `C:\Program Files\LALO AI\logs\`

## Distribution

### Final Checklist Before Release

- [ ] Tested on clean Windows 11 machine
- [ ] All core features working
- [ ] Documentation updated
- [ ] Version number correct
- [ ] License agreement included
- [ ] Icon present and correct
- [ ] Installer signed (optional, for production)

### Code Signing (Optional, Recommended for Production)

To avoid Windows SmartScreen warnings:

1. Obtain a code signing certificate
2. Install it on your build machine
3. Add to `lalo-ai-setup.iss`:

```ini
[Setup]
SignTool=signtool sign /f "your-certificate.pfx" /p "password" /t http://timestamp.digicert.com $f
```

### Hosting & Distribution

- Upload to secure download server
- Provide SHA256 hash for verification:
  ```powershell
  Get-FileHash dist\LALO-AI-Setup-1.0.0.exe -Algorithm SHA256
  ```
- Include hash in download page for users to verify

## Next Steps

After Windows installer is working:

1. **macOS Installer**
   - Create .app bundle
   - Use create-dmg or pkgbuild

2. **Linux Installer**
   - Create AppImage
   - Or .deb/.rpm packages

## Support

For build issues:
- Check Inno Setup documentation: https://jrsoftware.org/ishelp/
- Email: support@laloai.com
