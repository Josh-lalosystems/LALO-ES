# Windows Installer Readiness Checklist

Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

**Last Updated:** 2025-10-05
**Status:** ⏳ WAITING FOR TESTS TO PASS

---

## ✅ Installer Components (Ready)

### Infrastructure Files
- [x] **Inno Setup Script** - `installer/windows/lalo-ai-setup.iss`
- [x] **Start Script** - `installer/windows/start.bat`
- [x] **First Run Setup** - `installer/windows/first_run.bat`
- [x] **Dependency Installer** - `installer/windows/install_deps.bat`
- [x] **Configuration Template** - `installer/windows/.env.example`
- [x] **Pre-Install Readme** - `installer/windows/readme-before-install.txt`
- [x] **Post-Install Readme** - `installer/windows/readme-after-install.txt`
- [x] **Build Guide** - `installer/windows/BUILD_INSTALLER.md`

### Python Environment
- [x] **Python 3.11.9 Embeddable** - Downloaded and configured
  - Location: `installer/windows/python-3.11.9-embed-amd64/`
  - Size: ~10.7 MB
  - pip enabled: ✅ (`import site` uncommented in python311._pth)
  - Tested: ✅ (version check passed)

### Frontend Build
- [x] **Production Build** - `lalo-frontend/build/`
  - Size: 192.75 KB (gzipped)
  - TypeScript errors: Fixed
  - Build status: Clean (minor ESLint warnings only)

### Backend Code
- [x] **Application** - `app.py`
- [x] **Core Services** - `core/` directory
- [x] **Scripts** - `scripts/` directory (with `--auto-confirm` flag added)
- [x] **Requirements** - `requirements.txt`
- [x] **License** - `LICENSE` (proprietary)
- [x] **Documentation** - `README.md`, `docs/`

### AI Models (Downloaded)
- [x] **8 Models Ready** (~20 GB total)
  - bge-small (133 MB) - Embeddings
  - qwen-0.5b (352 MB) - Validation
  - tinyllama (669 MB) - General
  - deepseek-coder (4.0 GB) - Coding
  - openchat (4.37 GB) - Research
  - mistral-instruct (4.37 GB) - Research
  - phi-2 (1.60 GB) - Routing/General
  - metamath (4.37 GB) - Math

---

## ⏳ BLOCKING ISSUES (Must Be Fixed Before Build)

### 🔴 Python Tests Failing
**Status:** ⏳ Other team is running full test suite

**What We're Waiting For:**
1. ConfidenceModel.score() - Evasive text detection implementation
2. Router heuristics - Design/architecture keyword handling
3. UnifiedRequestHandler - Empty request validation
4. All unit tests passing
5. Integration tests passing

**Action Required:**
- ❌ **DO NOT build installer until tests pass**
- ✅ Wait for other team to complete backend fixes
- ✅ Verify all tests green
- ✅ Then rebuild frontend (if APIs changed)
- ✅ Then build installer

---

## ⚠️ Optional Items (Can Skip for First Build)

### Application Icon
- [ ] **lalo-icon.ico** - Not created yet
  - **Impact:** Windows will use generic icon
  - **Workaround:** Comment out icon lines in .iss file
  - **Priority:** Low (cosmetic only)

### Code Signing
- [ ] **Certificate** - Not configured
  - **Impact:** Windows SmartScreen warning on first run
  - **Workaround:** Users click "Run anyway"
  - **Priority:** Medium (required for public distribution)

### Liquid AI Models
- [ ] **LFM2 Models** - GGUF versions not yet available
  - liquid-lfm2-1.2b-rag
  - liquid-lfm2-350m-math/tool
  - liquid-lfm2-vision
  - **Impact:** Missing specialized models
  - **Workaround:** Using alternatives (phi-2 for routing, metamath for math)
  - **Priority:** Low (nice to have)

---

## 📋 Pre-Build Verification Steps

Once tests pass, verify these before building:

### 1. Backend Tests
```bash
# Run full test suite
pytest tests/ -v

# Check for failures
echo $?  # Should be 0
```

### 2. Frontend Build
```bash
cd lalo-frontend
npm run build

# Verify no errors
ls -lh build/
```

### 3. Model Availability
```bash
# Check models directory
ls -lh models/

# Should see 8+ subdirectories
```

### 4. Python Embeddable
```bash
# Verify Python works
installer/windows/python-3.11.9-embed-amd64/python.exe --version

# Should output: Python 3.11.9
```

### 5. Inno Setup Installed
```bash
# Windows only - check if installed
ls "C:/Program Files (x86)/Inno Setup 6/ISCC.exe"
```

---

## 🔨 Build Process (After Tests Pass)

### Step 1: Final Frontend Build
```bash
cd lalo-frontend
npm install  # Ensure latest dependencies
npm run build
```

### Step 2: Verify Backend
```bash
# Run quick smoke test
python app.py &
sleep 5
curl http://localhost:8000/health
kill %1
```

### Step 3: Build Installer

**Option A: GUI Method**
1. Open Inno Setup Compiler
2. File → Open → `installer/windows/lalo-ai-setup.iss`
3. Build → Compile
4. Wait for completion
5. Check output: `dist/LALO-AI-Setup-1.0.0.exe`

**Option B: Command Line**
```powershell
# From LALOai-main root
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\windows\lalo-ai-setup.iss
```

### Step 4: Verify Installer Created
```bash
ls -lh dist/LALO-AI-Setup-1.0.0.exe

# Should be ~500 MB (without models)
```

---

## 🧪 Testing Plan (After Build)

### Phase 1: Development Machine (30 min)
- [ ] Run installer
- [ ] Install to test directory (not Program Files)
- [ ] Verify first_run.bat executes
- [ ] Check dependencies install successfully
- [ ] Verify database initializes
- [ ] Test application starts
- [ ] Browser opens to localhost:8000
- [ ] Can log in with demo token
- [ ] Can navigate between pages

### Phase 2: Clean Windows 11 Laptop (2 hours)
**CRITICAL TEST - Simulates end user experience**

**Pre-Test Setup:**
- [ ] Blank Windows 11 installation
- [ ] No Python installed
- [ ] No development tools
- [ ] No Visual Studio, Git, etc.

**Installation Test:**
- [ ] Copy installer to test machine
- [ ] Run as Administrator
- [ ] Follow installation wizard
- [ ] Accept default installation path
- [ ] Complete first-run setup
- [ ] Download models (or skip)

**Functionality Test:**
- [ ] Desktop shortcut created
- [ ] Start menu entry created
- [ ] Application launches successfully
- [ ] Server starts on port 8000
- [ ] Browser opens automatically
- [ ] Login page displays
- [ ] Demo token works
- [ ] Settings page loads
- [ ] Can navigate all pages
- [ ] Local models load (if downloaded)
- [ ] Can send test AI request
- [ ] Response received successfully
- [ ] Usage tracking works
- [ ] No console errors

**Uninstall Test:**
- [ ] Uninstall via Windows Settings
- [ ] All files removed
- [ ] No registry leftovers
- [ ] Desktop shortcut removed
- [ ] Start menu entry removed

---

## 🚀 Distribution Checklist (After Testing)

Once testing passes on clean Windows 11:

- [ ] **Generate SHA256 hash**
  ```powershell
  Get-FileHash dist\LALO-AI-Setup-1.0.0.exe -Algorithm SHA256
  ```

- [ ] **Create release notes**
  - Version number
  - New features
  - Bug fixes
  - Known issues
  - System requirements

- [ ] **Update documentation**
  - Installation guide
  - User manual
  - Troubleshooting guide

- [ ] **Code signing** (optional, for public release)
  - Obtain certificate
  - Sign installer
  - Verify signature

- [ ] **Upload to distribution server**
  - Secure download location
  - Include SHA256 hash
  - Provide installation instructions

---

## 📊 Current Status Summary

| Item | Status | Blocking? |
|------|--------|-----------|
| Frontend Build | ✅ Ready | No |
| Backend Code | ⏳ Tests Running | **YES** |
| Python Embeddable | ✅ Ready | No |
| Installer Scripts | ✅ Ready | No |
| Documentation | ✅ Ready | No |
| Models Downloaded | ✅ Ready | No |
| Application Icon | ⚠️ Missing | No |
| Code Signing | ⚠️ Not Configured | No |
| **TESTS PASSING** | ❌ **FAILING** | **YES - BLOCKER** |

---

## ⏭️ Next Actions (In Order)

1. ⏳ **WAIT** - Let other team finish backend fixes and testing
2. ⏳ **VERIFY** - Confirm all Python tests pass
3. ✅ **REBUILD** - Frontend (if backend APIs changed)
4. ✅ **BUILD** - Create installer with Inno Setup
5. ✅ **TEST** - Development machine first
6. ✅ **TEST** - Clean Windows 11 laptop (critical)
7. ✅ **DISTRIBUTE** - Only after all tests pass

---

## 🔴 CRITICAL REMINDER

**DO NOT BUILD INSTALLER UNTIL:**
- ✅ All Python unit tests pass
- ✅ All integration tests pass
- ✅ Backend changes complete and verified
- ✅ Frontend rebuilt (if needed)
- ✅ Quick smoke test successful

**Building with failing tests will result in:**
- Broken installer
- Bad user experience on clean Windows 11
- Wasted time rebuilding
- Potential reputation damage

**Be patient. Wait for green tests. Build once, correctly.** ✅

---

## 📞 Questions?

- Technical issues: Check [BUILD_INSTALLER.md](windows/BUILD_INSTALLER.md)
- Test failures: Wait for other team to complete
- Installer bugs: Test on dev machine first, then clean Windows 11

**Remember:** The installer will work perfectly *once the backend tests pass*. All infrastructure is ready and waiting.
