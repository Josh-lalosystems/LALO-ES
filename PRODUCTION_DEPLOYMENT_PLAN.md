# Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of LALO AI Platform and is protected by copyright law.
# Unauthorized copying, modification, distribution, or use of this software,
# via any medium, is strictly prohibited without the express written permission
# of LALO AI SYSTEMS, LLC.
#

# LALO AI - Production Deployment Plan

**Date:** October 5, 2025
**Goal:** Create production-ready installers for Windows, macOS, and Linux
**Phase 1 Focus:** Windows 11 (blank laptop testing)

---

## 🎯 Your Requirements - Confirmed

### Installation Strategy
✅ **Option A: Small installer + download models on first run**
- Installer: ~50 MB
- Models: Download on first launch (~20-30 GB)
- Resumable downloads
- Progress indicators
- Offline mode after setup

### Testing Strategy
1. **Development machine:** Test all features (DONE - in progress)
2. **Blank Windows 11 laptop:** Clean install test (NEXT)
3. **Cross-platform:** macOS and Linux installers (FUTURE)

### Model Requirements
✅ **Math:** Liquid AI LFM2-350M-Math + MetaMath
✅ **Finance:** Mistral + Math models
✅ **Coding:** DeepSeek-Coder
✅ **Research:** OpenChat + Mistral
✅ **Routing/Orchestration:** Liquid AI LFM2-1.2B-Tool + Phi-2
✅ **RAG:** BGE-Small + Liquid AI LFM2-1.2B-RAG
✅ **Vision-to-Language:** Liquid AI LFM2-VL-1.6B
✅ **General:** TinyLlama
✅ **Validation:** Qwen-0.5b

---

## 📦 Complete Model Catalog

### Tier 1: Essential Models (Priority 1) - ~15 GB

| Model | Size | Status | Purpose |
|-------|------|--------|---------|
| **TinyLlama-1.1B** | 669 MB | ✅ Downloaded | General chat, quick Q&A |
| **DeepSeek-Coder-6.7B** | 4.0 GB | ✅ Downloaded | Code generation, debugging |
| **OpenChat-3.5** | 4.37 GB | ✅ Downloaded | Research, business intelligence |
| **Mistral-7B-Instruct** | 4.37 GB | ✅ Downloaded | Reasoning, analysis, reports |
| **Qwen-0.5B** | 352 MB | ✅ Downloaded | Confidence validation |
| **BGE-Small** | 133 MB | ✅ Downloaded | Text embeddings for RAG |
| **Phi-2** | 1.6 GB | ⏳ Downloading | Routing, function calling |
| **MetaMath-7B** | 4.37 GB | ⏳ Downloading | Advanced mathematics |

### Tier 2: Liquid AI Specialized Models (Priority 1) - ~3 GB

| Model | Size | Status | Purpose |
|-------|------|--------|---------|
| **LFM2-1.2B-Tool** | ~700 MB | ⏸️ To Add | Precise tool calling, orchestration |
| **LFM2-350M-Math** | ~200 MB | ⏸️ To Add | Math reasoning (ultra-fast) |
| **LFM2-1.2B-RAG** | ~700 MB | ⏸️ To Add | Retrieval-augmented generation |
| **LFM2-VL-1.6B** | ~1.0 GB | ⏸️ To Add | Vision-to-language (image understanding) |

### Tier 3: Optional Advanced Models (Priority 2) - ~10 GB

| Model | Size | Status | Purpose |
|-------|------|--------|---------|
| **CodeLlama-7B** | 4.24 GB | Optional | Alternative code model |
| **WizardCoder-7B** | 4.0 GB | Optional | Code optimization |
| **Mixtral-8x7B** | 26 GB | Optional | Advanced reasoning (requires 32GB+ RAM) |

**Total Essential:** ~18 GB (Tier 1 + Tier 2)
**Total with Optional:** ~28 GB

---

## 🔧 Technical Implementation Plan

### Phase 1: Windows Development & Testing (THIS WEEK)

#### Day 1: Model Setup (TODAY - In Progress)
- [x] Download Tier 1 models (6/8 complete)
- [ ] Download phi-2 and metamath (in progress)
- [ ] Add Liquid AI models to download script
- [ ] Download Liquid AI models
- [ ] Test all models individually
- [ ] Create model testing script

#### Day 2: End-to-End Testing (TOMORROW)
- [ ] Test each model with specialty prompts
- [ ] Test multi-model orchestration
- [ ] Test routing between models
- [ ] Test RAG with BGE-Small
- [ ] Test vision model (if images provided)
- [ ] Document any issues/bugs
- [ ] Performance benchmarks

#### Day 3-4: Windows Installer (THIS WEEK)
- [ ] Download & install Inno Setup
- [ ] Download Python 3.11 embeddable
- [ ] Build frontend production: `npm run build`
- [ ] Create installer script
- [ ] Implement model auto-download on first run
- [ ] Add progress indicators
- [ ] Add error handling
- [ ] Build LALO-AI-Setup.exe

#### Day 5: Clean Machine Testing (WEEKEND)
- [ ] Test on blank Windows 11 laptop
- [ ] Document installation process
- [ ] Fix any issues found
- [ ] Create user guide
- [ ] Record video tutorial

### Phase 2: Cross-Platform (NEXT WEEK)

#### macOS Installer
**Tools:** DMG + pkg installer
- Python 3.11 framework build
- .app bundle structure
- Code signing (Apple Developer Account)
- Notarization for Gatekeeper

#### Linux Installer
**Tools:** AppImage or .deb/.rpm
- Python virtual environment
- systemd service
- Desktop entry files
- Multiple distro support (Ubuntu, Fedora, Arch)

---

## 📝 Updated Download Script - Liquid AI Integration

Let me update `scripts/download_all_production_models.py` to include Liquid AI models:

```python
# Add to MODELS dictionary:

# ========================================================================
# LIQUID AI SPECIALIZED MODELS (New!)
# ========================================================================
"liquid-lfm2-tool": {
    "repo_id": "LiquidAI/LFM2-350M-Extract-GGUF",  # Tool-use variant
    "filename": "lfm2-350m-extract-q4_k_m.gguf",
    "size": "~200 MB",
    "description": "Precise tool calling and function extraction (Liquid AI)",
    "specialty": "routing",
    "priority": 1,
    "license": "Liquid AI License"
},

"liquid-lfm2-math": {
    "repo_id": "LiquidAI/LFM2-350M-Math-GGUF",
    "filename": "lfm2-350m-math-q4_k_m.gguf",
    "size": "~200 MB",
    "description": "Ultra-fast math reasoning (Liquid AI)",
    "specialty": "math",
    "priority": 1,
    "license": "Liquid AI License"
},

"liquid-lfm2-rag": {
    "repo_id": "LiquidAI/LFM2-1.2B-RAG",
    "filename": "model.safetensors",  # Note: May need GGUF conversion
    "size": "~700 MB",
    "description": "Retrieval-augmented generation (Liquid AI)",
    "specialty": "rag",
    "priority": 1,
    "license": "Liquid AI License",
    "model_type": "safetensors"  # Special handling needed
},

"liquid-lfm2-vision": {
    "repo_id": "LiquidAI/LFM2-VL-1.6B",
    "filename": "model.safetensors",  # Vision model
    "size": "~1.0 GB",
    "description": "Vision-to-language understanding (Liquid AI)",
    "specialty": "vision",
    "priority": 2,  # Optional for now (needs image processing pipeline)
    "license": "Liquid AI License",
    "model_type": "safetensors"
},
```

**Note:** Liquid AI RAG and Vision models use safetensors format. We have 2 options:

**Option A:** Use as-is with transformers library
- Requires `transformers`, `torch`, `safetensors` packages
- More memory overhead
- Slower inference

**Option B:** Convert to GGUF
- Use llama.cpp converter
- Faster inference
- Lower memory usage
- Recommended approach

---

## 🛠️ Windows Installer Architecture (Option A)

### User Experience Flow

```
1. User downloads LALO-AI-Setup.exe (50 MB)
   ↓
2. Runs installer (admin required)
   ↓
3. Installer creates folder structure
   ↓
4. Desktop shortcut created
   ↓
5. User double-clicks "LALO AI"
   ↓
6. First-run wizard appears:
   ┌────────────────────────────────────┐
   │  LALO AI - First Time Setup        │
   ├────────────────────────────────────┤
   │  Welcome! To use LALO AI, we need  │
   │  to download AI models (~20 GB).   │
   │                                    │
   │  [ ] Essential Models (18 GB)      │
   │  [ ] Optional Models (10 GB)       │
   │                                    │
   │  Disk space available: 250 GB      │
   │                                    │
   │  [Cancel]  [Download & Continue]   │
   └────────────────────────────────────┘
   ↓
7. Download progress shown:
   ┌────────────────────────────────────┐
   │  Downloading Models...             │
   ├────────────────────────────────────┤
   │  TinyLlama: [████████] 100%        │
   │  DeepSeek-Coder: [████░░] 60%      │
   │  Overall: 3.2 GB / 18 GB (18%)     │
   │                                    │
   │  Speed: 5.2 MB/s | ETA: 45 min     │
   │                                    │
   │  [Pause]  [Cancel]                 │
   └────────────────────────────────────┘
   ↓
8. Server starts automatically
   ↓
9. Browser opens to http://localhost:8000
   ↓
10. User clicks "Get Demo Token" and starts using!
```

### Installation Directory Structure

```
C:\Program Files\LALO AI\
├── python311\                  # Embedded Python (10 MB)
│   ├── python.exe
│   ├── python311.dll
│   └── Lib\
├── app\                        # LALO application (100 MB)
│   ├── core\
│   │   ├── services\
│   │   ├── routes\
│   │   └── models\
│   ├── lalo-frontend\
│   │   └── build\              # Production React build
│   ├── scripts\
│   │   ├── download_models.py
│   │   └── first_run_setup.py
│   ├── app.py
│   ├── requirements.txt
│   └── .env.example
├── start.bat                   # Launches server
├── first_run.bat               # First-time setup wizard
├── uninstall.exe
└── README.txt

C:\Users\{Username}\AppData\Local\LALO AI\
├── config\
│   ├── settings.json
│   └── .env                    # User's environment config
├── models\                     # Downloaded on first run
│   ├── tinyllama\
│   ├── deepseek-coder\
│   ├── openchat\
│   ├── mistral-instruct\
│   ├── phi-2\
│   ├── metamath\
│   ├── liquid-lfm2-tool\
│   ├── liquid-lfm2-math\
│   └── ... (more models)
├── lalo.db                     # SQLite database
└── logs\
    ├── app.log
    └── models.log

Desktop\
└── LALO AI.lnk                 # Shortcut
```

### Inno Setup Script (lalo-installer.iss)

```iss
[Setup]
AppName=LALO AI
AppVersion=1.0.0
AppPublisher=LALO AI LLC
AppPublisherURL=https://lalo-ai.com
DefaultDirName={autopf}\LALO AI
DefaultGroupName=LALO AI
OutputBaseFilename=LALO-AI-Setup
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
SetupIconFile=lalo-icon.ico
UninstallDisplayIcon={app}\lalo-icon.ico
WizardStyle=modern
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Embedded Python
Source: "python-3.11-embed\*"; DestDir: "{app}\python311"; Flags: recursesubdirs

; LALO Application
Source: "LALOai-main\*"; DestDir: "{app}\app"; Flags: recursesubdirs; \
  Excludes: "venv,node_modules,__pycache__,*.pyc,.git,.env,lalo.db,models"

; Launcher scripts
Source: "start.bat"; DestDir: "{app}"; Flags: isreadme
Source: "first_run.bat"; DestDir: "{app}";

; Icon
Source: "lalo-icon.ico"; DestDir: "{app}";

; Documentation
Source: "README.txt"; DestDir: "{app}"; Flags: isreadme
Source: "LICENSE.txt"; DestDir: "{app}";

[Dirs]
Name: "{localappdata}\LALO AI\config"; Permissions: users-full
Name: "{localappdata}\LALO AI\models"; Permissions: users-full
Name: "{localappdata}\LALO AI\logs"; Permissions: users-full

[Icons]
Name: "{commondesktop}\LALO AI"; Filename: "{app}\start.bat"; \
  IconFilename: "{app}\lalo-icon.ico"; WorkingDir: "{app}\app"
Name: "{group}\LALO AI"; Filename: "{app}\start.bat"; \
  IconFilename: "{app}\lalo-icon.ico"
Name: "{group}\Uninstall LALO AI"; Filename: "{uninstallexe}"

[Run]
; Install Python dependencies
Filename: "{app}\python311\python.exe"; \
  Parameters: "-m pip install --no-index --find-links {app}\app\wheels -r {app}\app\requirements.txt"; \
  StatusMsg: "Installing dependencies..."; Flags: runhidden

; Create .env file from example
Filename: "{cmd}"; \
  Parameters: "/c copy ""{app}\app\.env.example"" ""{localappdata}\LALO AI\config\.env"""; \
  Flags: runhidden

; Run first-time setup on finish
Filename: "{app}\first_run.bat"; \
  Description: "Download AI models and start LALO AI"; \
  Flags: postinstall nowait skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  AvailableSpace: Extended;
begin
  Result := True;

  { Check disk space (need ~25 GB) }
  AvailableSpace := DiskSpaceGB('C');

  if AvailableSpace < 25.0 then
  begin
    MsgBox('Insufficient disk space. LALO AI requires at least 25 GB free space. ' + #13#10 +
           'Current available space: ' + FloatToStr(AvailableSpace) + ' GB',
           mbError, MB_OK);
    Result := False;
  end;
end;

function DiskSpaceGB(Drive: String): Extended;
begin
  Result := DiskSpaceMByte(Drive) / 1024.0;
end;
```

### start.bat (Server Launcher)

```bat
@echo off
setlocal

REM Change to app directory
cd /d "%~dp0app"

REM Check if first run (models not downloaded)
if not exist "%LOCALAPPDATA%\LALO AI\models\tinyllama" (
    echo First-time setup required!
    echo.
    echo Please run "LALO AI First Run Setup" from the Start menu.
    pause
    exit /b 1
)

echo ====================================
echo    LALO AI - Starting Server
echo ====================================
echo.

REM Set environment variables
set PYTHONPATH=%~dp0app
set MODELS_DIR=%LOCALAPPDATA%\LALO AI\models
set DATABASE_URL=sqlite:///%LOCALAPPDATA%\LALO AI\lalo.db

REM Start backend server
echo Starting backend server...
start /b "" "%~dp0python311\python.exe" app.py > "%LOCALAPPDATA%\LALO AI\logs\app.log" 2>&1

REM Wait for server to start
echo Waiting for server to start...
timeout /t 5 /nobreak > nul

REM Check if server is running
powershell -Command "(New-Object Net.WebClient).DownloadString('http://localhost:8000')" > nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Server started!
    echo Opening browser...
    start http://localhost:8000
) else (
    echo.
    echo [ERROR] Server failed to start.
    echo Check logs at: %LOCALAPPDATA%\LALO AI\logs\app.log
)

echo.
echo Server is running in the background.
echo Close this window to stop the server.
echo.
pause

REM Kill server when user closes window
taskkill /f /im python.exe /fi "WINDOWTITLE eq app.py" 2>nul
```

### first_run.bat (Model Downloader)

```bat
@echo off
setlocal

echo ====================================
echo   LALO AI - First Run Setup
echo ====================================
echo.
echo This will download AI models (~18 GB).
echo Estimated time: 30-60 minutes
echo.
echo Models will be saved to:
echo %LOCALAPPDATA%\LALO AI\models
echo.
pause

REM Change to app directory
cd /d "%~dp0app"

REM Run model download script with GUI
"%~dp0python311\pythonw.exe" scripts\first_run_setup_gui.py

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Setup complete!
    echo.
    echo You can now start LALO AI from the desktop shortcut.
    pause
) else (
    echo.
    echo [ERROR] Setup failed or was cancelled.
    echo.
    echo You can try again later from the Start menu.
    pause
)
```

---

## 🧪 Testing Plan

### Test Cases for Blank Windows 11 Laptop

**Pre-requisites:**
- Fresh Windows 11 installation
- No Python installed
- No other development tools
- Internet connection
- At least 30 GB free space

**Test Procedure:**

1. **Download Installer**
   - [ ] Download LALO-AI-Setup.exe
   - [ ] Verify file size (~50 MB)
   - [ ] Check SHA256 checksum

2. **Installation**
   - [ ] Run installer (requires admin)
   - [ ] Accept license
   - [ ] Choose installation directory
   - [ ] Wait for installation to complete
   - [ ] Verify desktop shortcut created

3. **First Run**
   - [ ] Double-click desktop shortcut
   - [ ] See first-run wizard
   - [ ] Select models to download
   - [ ] Start download
   - [ ] Verify download progress displays correctly
   - [ ] Verify download speed is reasonable
   - [ ] Test pause/resume functionality

4. **Model Download**
   - [ ] Download completes without errors
   - [ ] All models present in `AppData\Local\LALO AI\models\`
   - [ ] Verify model file sizes match expected

5. **Server Startup**
   - [ ] Server starts automatically after download
   - [ ] Browser opens to http://localhost:8000
   - [ ] Frontend loads correctly
   - [ ] No console errors visible

6. **Functionality Testing**
   - [ ] Get demo token works
   - [ ] Can access all pages (Request, Settings, Usage, etc.)
   - [ ] Model selector shows all downloaded models
   - [ ] Can send request to each model
   - [ ] Responses are coherent
   - [ ] Streaming works (toggle switch)
   - [ ] Routing info displays correctly

7. **Performance Testing**
   - [ ] First model load: < 30 seconds
   - [ ] Subsequent requests: < 10 seconds
   - [ ] Memory usage stays under 8 GB
   - [ ] CPU usage reasonable
   - [ ] No memory leaks after 30 minutes

8. **Shutdown/Restart**
   - [ ] Close server window
   - [ ] Server stops cleanly
   - [ ] Restart from desktop shortcut
   - [ ] Models still available (no re-download)
   - [ ] Previous chat history preserved

9. **Uninstallation**
   - [ ] Run uninstaller from Start menu
   - [ ] All files removed from Program Files
   - [ ] Option to keep models/database
   - [ ] Desktop shortcut removed
   - [ ] No orphaned processes

---

## 📊 Success Metrics

### Installation
- ✅ Installer size: < 100 MB
- ✅ Installation time: < 5 minutes
- ✅ No errors on clean Windows 11

### First Run
- ✅ Model download: Resumable
- ✅ Total download time: < 60 minutes (on average internet)
- ✅ Progress indicators accurate

### Usage
- ✅ Server starts in < 30 seconds
- ✅ First AI response: < 60 seconds (includes model load)
- ✅ Subsequent responses: < 15 seconds average
- ✅ Memory usage: < 8 GB with 3 models loaded
- ✅ Works offline after initial setup

### Reliability
- ✅ Runs for 24+ hours without crashes
- ✅ Handles multiple concurrent requests
- ✅ Graceful error handling
- ✅ Uninstalls cleanly

---

## 🚧 Known Limitations & Future Work

### Current Limitations
1. **Windows Only** (for now)
2. **No GPU Support** (CPU-only in v1.0)
3. **Vision Model** requires image processing pipeline (Phase 2)
4. **No Auto-Updates** (manual re-install for updates)

### Future Enhancements
1. **GPU Acceleration** (CUDA/ROCm support)
2. **macOS & Linux Installers**
3. **Auto-Update Mechanism**
4. **Model Marketplace** (download additional models from UI)
5. **Cloud Sync** (optional backup to cloud)
6. **Multi-User Support** (for organizations)
7. **Docker Container** (for easier deployment)

---

## 📅 Timeline

### This Week (Windows Focus)
- **Monday-Tuesday:** Download & test all models
- **Wednesday-Thursday:** Build Windows installer
- **Friday:** Test on blank Windows 11 laptop
- **Weekend:** Fix bugs, polish UI

### Next Week (Cross-Platform)
- **Monday-Tuesday:** macOS installer research & development
- **Wednesday-Thursday:** Linux installer (.deb and AppImage)
- **Friday:** Cross-platform testing

### Week 3 (Distribution)
- Create documentation
- Record video tutorials
- Set up GitHub Releases
- Announce to first users

---

## ✅ Current Status

**What Works Right Now:**
- 6 core models downloaded and ready
- Backend server runs
- Frontend interface functional
- Streaming responses working
- Basic orchestration implemented

**In Progress:**
- Downloading phi-2 and metamath
- Adding Liquid AI models to catalog

**Next Steps:**
1. Complete model downloads
2. Test all models
3. Build Windows installer
4. Test on clean machine

---

**You're on track to have a distributable Windows installer by end of week!**

Let me know when you're ready to:
1. Test the models we've already downloaded
2. Start building the installer
3. Add more specialized models

I'm ready to help with whichever you want to tackle first.
