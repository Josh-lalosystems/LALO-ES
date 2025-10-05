# Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of LALO AI Platform and is protected by copyright law.
# Unauthorized copying, modification, distribution, or use of this software,
# via any medium, is strictly prohibited without the express written permission
# of LALO AI SYSTEMS, LLC.
#

# LALO AI - Live Testing & Installer Distribution Plan

**Date:** October 5, 2025
**Status:** In Progress
**Goal:** Enable live local inference testing and create distributable installer

---

## Current Status

### ✅ Completed
- [x] llama-cpp-python installed (v0.3.2 with CPU support)
- [x] huggingface-hub installed
- [x] Comprehensive model download script created
- [x] local_llm_service.py updated with 7 specialized models
- [x] Streaming support implemented (backend + frontend)
- [x] Phase 3 frontend integration complete

### ⏳ In Progress
- [ ] Downloading Priority 1 models (~19 GB)
  - [x] bge-small (133 MB) - Embeddings
  - [x] qwen-0.5b (352 MB) - Validation
  - [x] tinyllama (669 MB) - General
  - [ ] liquid-tool (752 MB) - **FAILED (401 error)**
  - [ ] deepseek-coder (4.0 GB) - Downloading...
  - [ ] deepseek-math (4.37 GB) - Queued
  - [ ] openchat (4.37 GB) - Queued
  - [ ] mistral-instruct (4.37 GB) - Queued

### 🔧 To Do
- [ ] Fix liquid-tool download (find alternative source)
- [ ] Complete model downloads
- [ ] Test each model with real inference
- [ ] Create end-to-end testing script
- [ ] Build Windows installer
- [ ] Create user documentation

---

## Phase 1: Complete Model Setup

### 1.1 Fix Liquid-Tool Download

**Problem:** Liquid-1.2B-Tool from second-state repo returns 401 (unauthorized)

**Solutions:**
```bash
# Option A: Use alternative function-calling model
phi-2 (Microsoft) - 1.6 GB, MIT license, supports function calling

# Option B: Try different Liquid repo
QuantFactory/Liquid-1.2B-Tool-GGUF (community quantization)

# Option C: Use Hermes-2-Pro for function calling
NousResearch/Hermes-2-Pro-Llama-3-8B-GGUF - 4.8 GB
```

**Action:** Use Phi-2 as replacement (already in catalog as P2 model)

### 1.2 Model Download Completion

**Current Download Status:**
```
[✓] bge-small (133 MB) - Downloaded
[✓] qwen-0.5b (352 MB) - Downloaded
[✓] tinyllama (669 MB) - Downloaded
[✗] liquid-tool (752 MB) - Failed, replacing with phi-2 (1.6 GB)
[...] deepseek-coder (4.0 GB) - In progress
[...] deepseek-math (4.37 GB) - Queued
[...] openchat (4.37 GB) - Queued
[...] mistral-instruct (4.37 GB) - Queued
```

**Total Download:** ~20 GB (with phi-2 replacement)
**Estimated Time:** 30-60 minutes (depending on connection speed)

---

## Phase 2: Model Testing

### 2.1 Individual Model Tests

Create test script: `scripts/test_all_models.py`

```python
"""Test each model with specialty-specific prompts"""

TEST_PROMPTS = {
    "math": "Calculate the compound interest on $10,000 at 5% annual rate for 3 years",
    "coding": "Write a Python function to find the longest palindrome in a string",
    "research": "Summarize the key benefits of renewable energy for businesses",
    "general": "Explain quantum computing in simple terms",
    "validation": "Score this output for accuracy: '2+2=5'",
    "routing": "Classify this request: 'Create a financial model for startup valuation'"
}

def test_model(model_name, specialty):
    """Test a model with its specialty prompt"""
    prompt = TEST_PROMPTS.get(specialty, TEST_PROMPTS["general"])

    # Load model
    # Generate response
    # Measure: speed (tokens/sec), memory usage, quality
    # Return test results
```

**Success Criteria:**
- Each model loads without errors
- Generates coherent responses
- Completes in reasonable time (< 60 seconds)
- Memory usage stays within limits

### 2.2 End-to-End Workflow Test

Test complete orchestration:

```python
"""
Test: Complex business request requiring multiple models
"""
REQUEST = """
Analyze the financial viability of a solar panel installation
for a manufacturing facility. Calculate ROI and generate a
Python script to model cash flows over 10 years.
"""

# Expected workflow:
# 1. Router (liquid-tool/phi-2) → classifies as "complex"
# 2. Orchestrator breaks into steps:
#    - Research (openchat) → solar panel economics
#    - Math (deepseek-math) → ROI calculation
#    - Code (deepseek-coder) → Python cash flow script
# 3. Confidence (qwen-0.5b) → validates final output
# 4. Return comprehensive response
```

**Test Cases:**
1. Math-only request: "What's 15% of $1,250?"
2. Code-only request: "Write a quicksort algorithm in Python"
3. Research-only request: "Explain blockchain technology"
4. Multi-step complex: Business analysis + calculations + code

---

## Phase 3: Windows Installer Creation

### 3.1 Installer Requirements

**User Experience Goal:**
- One-click install
- No manual dependency management
- Includes all models (or downloads on first run)
- Desktop shortcut
- Uninstaller

**Technology Options:**

| Tool | Pros | Cons | Recommendation |
|------|------|------|----------------|
| **Inno Setup** | Free, popular, good docs | Scripts only | ⭐ Best for scripted install |
| **NSIS** | Very customizable | Complex syntax | Good alternative |
| **PyInstaller + NSIS** | Bundles Python app | Large file size | For standalone .exe |
| **Electron + exe** | Modern UI | Huge file size (500MB+) | Overkill |

**Recommended:** Inno Setup

### 3.2 Installer Components

**What Gets Installed:**

```
LALO-AI-Installer.exe (20-30 MB installer that downloads models on first run)
  │
  ├── Program Files/LALO AI/
  │   ├── python311/ (embedded Python)
  │   ├── app/ (all LALO source code)
  │   ├── lalo-frontend/build/ (React app)
  │   ├── requirements.txt
  │   ├── start.bat (launches server)
  │   └── uninstall.exe
  │
  ├── AppData/Local/LALO AI/
  │   ├── models/ (downloaded on first run)
  │   ├── lalo.db (user database)
  │   └── logs/
  │
  └── Desktop/
      └── LALO AI.lnk (shortcut)
```

**Embedded Python:**
- Use embeddable Python 3.11 (10 MB)
- Include pip and virtualenv
- Pre-install core dependencies

**Model Handling:**
- Option A: Include models in installer (~20 GB installer)
- Option B: Download on first run (recommended)
  - Show progress dialog
  - Allow model selection
  - Resume if interrupted

### 3.3 Inno Setup Script

Create `installer/lalo-ai-installer.iss`:

```iss
[Setup]
AppName=LALO AI
AppVersion=1.0.0
DefaultDirName={pf}\LALO AI
DefaultGroupName=LALO AI
OutputBaseFilename=LALO-AI-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Files]
; Embedded Python
Source: "python-3.11.8-embed-amd64\*"; DestDir: "{app}\python"; Flags: recursesubdirs

; LALO application
Source: "LALOai-main\*"; DestDir: "{app}\lalo"; Flags: recursesubdirs; Excludes: "__pycache__,*.pyc,node_modules,venv"

; Start script
Source: "start.bat"; DestDir: "{app}"; Flags: isreadme

[Icons]
Name: "{commondesktop}\LALO AI"; Filename: "{app}\start.bat"; IconFilename: "{app}\lalo\icon.ico"
Name: "{group}\LALO AI"; Filename: "{app}\start.bat"
Name: "{group}\Uninstall LALO AI"; Filename: "{uninstallexe}"

[Run]
; Install dependencies on first run
Filename: "{app}\python\python.exe"; Parameters: "-m pip install -r {app}\lalo\requirements.txt"; StatusMsg: "Installing dependencies..."; Flags: runhidden

; Download models (optional)
Filename: "{app}\python\python.exe"; Parameters: "{app}\lalo\scripts\download_all_production_models.py --priority 1"; StatusMsg: "Downloading AI models (this may take a while)..."; Flags: runhidden postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if MsgBox('LALO AI requires approximately 20 GB of disk space for AI models. Do you want to continue?', mbConfirmation, MB_YESNO) = IDNO then
    Result := False;
end;
```

**start.bat:**
```bat
@echo off
echo Starting LALO AI Platform...
cd /d "%~dp0lalo"

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Start backend server
start /b python app.py

REM Wait 5 seconds for backend to start
timeout /t 5 /nobreak > nul

REM Open browser to frontend
start http://localhost:8000

echo LALO AI is running!
echo Close this window to stop the server.
pause
```

### 3.4 Building the Installer

**Prerequisites:**
1. Download Inno Setup: https://jrsoftware.org/isinfo.php
2. Download Python 3.11 embeddable: https://www.python.org/downloads/
3. Build LALO frontend: `cd lalo-frontend && npm run build`

**Build Steps:**
```bash
# 1. Prepare directory structure
mkdir installer
mkdir installer/python-3.11.8-embed-amd64
mkdir installer/LALOai-main

# 2. Copy Python embeddable
# Download from python.org and extract to installer/python-3.11.8-embed-amd64/

# 3. Copy LALO source (excluding venv, node_modules, etc.)
xcopy c:\IT\LALOai-main installer\LALOai-main /E /I /EXCLUDE:exclude.txt

# 4. Compile installer with Inno Setup
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\lalo-ai-installer.iss

# 5. Output: installer/Output/LALO-AI-Setup.exe
```

**exclude.txt:**
```
venv\
node_modules\
__pycache__\
*.pyc
.git\
.env
lalo.db
models\
```

---

## Phase 4: Testing & Distribution

### 4.1 Installer Testing Checklist

**Test on Clean Windows Machine:**
- [ ] Installer runs without errors
- [ ] Python embeds correctly
- [ ] Dependencies install successfully
- [ ] Models download (or prompt to download)
- [ ] Server starts on port 8000
- [ ] Browser opens to correct URL
- [ ] Login works (demo mode)
- [ ] AI requests complete successfully
- [ ] All models accessible
- [ ] Uninstaller removes everything

**Different Windows Versions:**
- [ ] Windows 10 (64-bit)
- [ ] Windows 11
- [ ] Windows Server 2019/2022

**Hardware Variations:**
- [ ] 8 GB RAM (minimum)
- [ ] 16 GB RAM (recommended)
- [ ] 32 GB+ RAM (optimal)
- [ ] CPU-only (no GPU)
- [ ] With NVIDIA GPU (if GPU support added)

### 4.2 User Documentation

Create `USER_GUIDE.md`:

```markdown
# LALO AI - User Guide

## Quick Start

1. **Download** LALO-AI-Setup.exe
2. **Run** installer (requires admin rights)
3. **Wait** for model downloads (~20 GB, 30-60 min)
4. **Launch** from Desktop shortcut
5. **Access** at http://localhost:8000

## First Use

### Demo Login
- Click "Get Demo Token" (no account needed)
- Full access to all features

### Select a Model
- **TinyLlama** - Fast general chat
- **DeepSeek-Math** - Math and finance
- **DeepSeek-Coder** - Code generation
- **OpenChat** - Research and analysis

### Ask a Question
Type your request and click Send. Examples:
- "Calculate 15% tip on $87.50"
- "Write a Python function to reverse a string"
- "Explain machine learning in simple terms"

## Model Specialties

| Model | Best For | Speed |
|-------|----------|-------|
| TinyLlama | Quick Q&A, chat | ⭐⭐⭐⭐⭐ |
| DeepSeek-Math | Finance, calculations | ⭐⭐⭐⭐ |
| DeepSeek-Coder | Programming tasks | ⭐⭐⭐⭐ |
| OpenChat | Research, analysis | ⭐⭐⭐⭐ |
| Mistral | Reports, reasoning | ⭐⭐⭐⭐ |

## Troubleshooting

**Server won't start:**
- Check port 8000 is not in use
- Run as administrator
- Check firewall settings

**Models not loading:**
- Ensure models downloaded (check `models/` folder)
- Verify 20+ GB free disk space
- Re-run model download script

**Slow responses:**
- Normal on first load (model loads into RAM)
- Subsequent requests faster
- Consider upgrading to 16 GB+ RAM
```

### 4.3 Distribution Methods

**Option 1: Direct Download**
- Host on website/GitHub releases
- Provide SHA256 checksum
- Clear system requirements

**Option 2: Microsoft Store**
- Pros: Trust, auto-updates, easy install
- Cons: Review process, fees, restrictions
- Timeline: 2-4 weeks approval

**Option 3: Chocolatey Package**
- For developers/IT admins
- Easy deployment across organizations
- Command: `choco install lalo-ai`

**Recommended:** Start with direct download, expand to stores later

---

## Phase 5: Post-Release

### 5.1 Monitoring & Feedback

**Telemetry (Optional, Opt-in):**
- Model usage statistics
- Error reports
- Performance metrics
- Feature requests

**Support Channels:**
- GitHub Issues
- Discord/Slack community
- Email support
- Documentation wiki

### 5.2 Updates & Maintenance

**Version Numbering:**
- Major.Minor.Patch (e.g., 1.0.0)
- Major: Breaking changes, new architecture
- Minor: New models, features
- Patch: Bug fixes, performance

**Auto-Update Mechanism:**
```python
# Check for updates on startup
def check_for_updates():
    current_version = "1.0.0"
    response = requests.get("https://lalo-ai.com/api/latest-version")
    latest_version = response.json()["version"]

    if latest_version > current_version:
        show_update_prompt(latest_version)
```

---

## Timeline Estimate

| Phase | Tasks | Time Estimate |
|-------|-------|---------------|
| **Phase 1** | Complete model downloads, fix liquid-tool | 2-4 hours |
| **Phase 2** | Test all models, end-to-end testing | 4-6 hours |
| **Phase 3** | Create installer, build scripts | 6-8 hours |
| **Phase 4** | Test installer on multiple machines | 4-6 hours |
| **Phase 5** | Documentation, distribution setup | 3-4 hours |
| **Total** | **From now to distributable installer** | **1-2 days** |

---

## Next Immediate Steps

### Right Now:
1. ✅ Wait for model downloads to complete (~30 min remaining)
2. ⏳ Fix liquid-tool (replace with phi-2 or alternative)
3. ⏳ Test each model individually

### Today:
4. Create test_all_models.py script
5. Run end-to-end orchestration test
6. Document any issues/bugs

### Tomorrow:
7. Download Python embeddable
8. Create Inno Setup script
9. Build first installer version
10. Test on clean machine

### This Week:
11. Refine installer based on testing
12. Write user documentation
13. Create video tutorial
14. Prepare for distribution

---

## Success Metrics

### Installer Quality:
- [ ] Installs in < 5 minutes (excluding model downloads)
- [ ] Works on fresh Windows 10/11 without errors
- [ ] User can chat with AI within 10 minutes of starting
- [ ] Uninstaller removes everything cleanly
- [ ] File size < 50 MB (excluding models)

### User Experience:
- [ ] No technical knowledge required
- [ ] Clear progress indicators
- [ ] Helpful error messages
- [ ] Works offline (after models downloaded)
- [ ] Responsive UI (< 1 second interactions)

### Performance:
- [ ] First response: < 30 seconds (including model load)
- [ ] Subsequent responses: < 10 seconds average
- [ ] Memory usage: < 8 GB for all models
- [ ] Supports 10+ concurrent requests

---

## Appendix: Alternative Approaches

### A. Docker Distribution
```bash
# Simpler for developers, harder for end-users
docker pull lalo-ai/platform:latest
docker run -p 8000:8000 lalo-ai/platform
```

### B. Cloud-First Hybrid
- Installer sets up local server
- Models hosted on cloud (faster download)
- User downloads only what they need

### C. Progressive Web App (PWA)
- No installer needed
- Access via browser
- Limited offline capabilities

**Verdict:** Windows installer remains best for target users (non-technical business users)

---

**Status:** Ready to proceed once model downloads complete
**Next:** Test all models → Create installer → Distribute
