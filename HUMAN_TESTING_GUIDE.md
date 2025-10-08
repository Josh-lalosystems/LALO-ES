# LALO AI - Internal Human Testing Guide

**Version**: Pre-Installer Alpha
**Date**: 2025-10-05
**Status**: Ready for Internal Testing

---

## ✅ What's Working

- **Local AI Inference** - tinyllama model generates responses (17s avg)
- **Router System** - Intelligently classifies requests
- **Confidence Scoring** - Validates output quality (0.89 avg)
- **RAG Pipeline** - Document ingestion, chunking, indexing
- **11 Local Models** - Downloaded and available
- **HTTP API** - FastAPI server with all endpoints
- **Frontend** - React UI built and serving

---

## 🚀 Quick Start (For Testers)

### Prerequisites

- Windows 10/11
- Python 3.11 installed
- **llama-cpp-python 0.3.2** (confirmed working with VS Build Tools/WSL)
- 8GB RAM minimum (16GB recommended)
- 20GB disk space (for models)

### Setup

1. **Clone/Pull Latest**:
   ```bash
   cd c:\IT\LALOai-main
   git pull origin main
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify llama-cpp-python**:
   ```bash
   python -c "import llama_cpp; print('llama-cpp-python', llama_cpp.__version__, 'working')"
   ```
   Expected: `llama-cpp-python 0.3.2 working`

4. **Check Environment Variables** (`.env` file):
   ```bash
   DEMO_MODE=false   # CRITICAL: Must be false for real inference
   JWT_SECRET_KEY=your-secret-key-here
   ENCRYPTION_KEY=your-encryption-key-here
   ```

5. **Verify Models Downloaded** (should be ~18GB):
   ```bash
   dir models /s
   ```
   Expected models:
   - tinyllama (637 MB)
   - qwen-0.5b (469 MB)
   - deepseek-coder (3.9 GB)
   - mistral-instruct (4.2 GB)
   - openchat (4.2 GB)
   - phi-2 (1.7 GB)

---

## 🧪 Testing Procedures

### Test 1: Server Startup

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

**Expected Output**:
```
[INFO] LALO AI System - Startup Validation
[OK] JWT_SECRET_KEY is configured
[OK] ENCRYPTION_KEY is valid
DEMO_MODE is disabled
[OK] Database found at lalo.db
[SUCCESS] Startup validation complete
Uvicorn running on http://127.0.0.1:8000
```

**✅ PASS**: Server starts without errors
**❌ FAIL**: Import errors, missing dependencies, database errors

---

### Test 2: Frontend Access

1. Open browser to: `http://localhost:8000`
2. Should see LALO AI login page
3. Click "Get Demo Token"
4. Should redirect to `/request` page

**✅ PASS**: Frontend loads and navigates
**❌ FAIL**: 404 errors, blank page, auth failures

---

### Test 3: Simple AI Request (CRITICAL)

Run automated test:
```bash
python test_local_model.py
```

**Expected Output**:
```
Testing Local Model Availability
1. Getting demo token... ✓ Got token
2. Getting available models... ✓ Available models: [tinyllama, qwen-0.5b, ...]
3. Testing chat request with tinyllama...
   Status: 200
   ✓ SUCCESS!
   Model used: tinyllama
   Response: [actual AI-generated text]
```

**✅ PASS**: Returns 200 OK with non-empty response from tinyllama
**❌ FAIL**: Timeout, 500 error, empty response, "(DEMO) Echo" response

**Troubleshooting**:
- If you see "(DEMO) Echo" → DEMO_MODE is still enabled in .env
- If timeout → Model loading issue (check logs)
- If empty response → Context window issue (try different model)

---

### Test 4: Model Loading Performance

Watch server logs during first request:

**Expected Timeline**:
```
[INFO] Router decision: path=simple, recommended_model=tinyllama
[INFO] Loading tinyllama from ./models/tinyllama/...
[INFO] ✓ tinyllama loaded successfully    # Should be < 1 second
[INFO] Request completed: time=17142ms     # Should be < 30 seconds
```

**Performance Benchmarks**:
- Model load: **< 1 second** ✅
- Inference: **< 30 seconds** ✅ (17s avg on CPU)
- Total request: **< 35 seconds** ✅

**❌ FAIL** if:
- Model load > 60 seconds
- Inference > 60 seconds
- Server crashes/OOM

---

### Test 5: Multiple Requests

Send 3 consecutive requests:

```bash
# Request 1
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2+2?", "model": "tinyllama"}'

# Request 2
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a haiku about AI", "model": "tinyllama"}'

# Request 3
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing", "model": "tinyllama"}'
```

**✅ PASS**: All 3 return 200 OK, model stays loaded (2nd/3rd requests faster)
**❌ FAIL**: Server crashes, memory leak, degrading performance

---

### Test 6: Document Upload (RAG)

1. Navigate to Document Upload page (if available in UI)
2. Upload a test PDF/Word/Excel file
3. Check server logs for:
   ```
   [INFO] Document quality score: XX
   [INFO] Chunks created: XX
   [INFO] Background indexer: enqueued job
   ```

**✅ PASS**: Document processed, chunks created
**❌ FAIL**: Import errors (missing openpyxl, python-docx, PyPDF2)

---

## 📊 Success Criteria for Alpha Release

### Must Pass (Blockers)
- [ ] Server starts without errors
- [ ] Frontend loads and is navigable
- [ ] Test 3 passes (real AI inference works)
- [ ] Performance within benchmarks
- [ ] No crashes on 3 consecutive requests

### Should Pass (Important)
- [ ] Document upload works
- [ ] Usage tracking records requests
- [ ] Confidence scoring > 0.7 average
- [ ] Models load < 1 second

### Nice to Have
- [ ] All 6 models tested and working
- [ ] Streaming responses functional
- [ ] Multi-model orchestration
- [ ] Tool execution (web search, etc.)

---

## 🐛 Known Issues

1. **Empty Responses** - qwen-0.5b context window too small (512 tokens)
   - **Workaround**: Use tinyllama or increase n_ctx in config

2. **First Request Slow** - Model loads on first use (expected)
   - **Not a bug**: Subsequent requests are faster

3. **Encryption Warnings** - "Failed to decrypt keys" in logs
   - **Not critical**: Demo keys use old encryption, API keys work fine

4. **Windows Console Unicode** - Checkmark (✓) characters fail
   - **Workaround**: Already handled in test scripts

---

## 📝 Testing Checklist

Print this and fill out:

```
Tester Name: ________________
Date: ________________
Environment: Windows ___

[ ] Test 1: Server Startup - PASS / FAIL
[ ] Test 2: Frontend Access - PASS / FAIL
[ ] Test 3: Simple AI Request - PASS / FAIL
    Response time: _____ seconds
    Response quality: Good / Poor
[ ] Test 4: Model Loading - PASS / FAIL
    Load time: _____ seconds
[ ] Test 5: Multiple Requests - PASS / FAIL
[ ] Test 6: Document Upload - PASS / FAIL

Notes/Issues Found:
_________________________________
_________________________________
_________________________________

Overall Assessment: READY / NEEDS WORK
```

---

## 🆘 Common Problems & Solutions

### "ModuleNotFoundError: No module named 'llama_cpp'"
**Solution**: Run `pip install llama-cpp-python`

### "DEMO_MODE is enabled" in logs
**Solution**: Edit `.env`, change `DEMO_MODE=true` to `DEMO_MODE=false`

### "Model file not found"
**Solution**: Run `python scripts/download_models.py` to download models

### "Port 8000 already in use"
**Solution**: Kill existing python processes:
```bash
tasklist | findstr python
taskkill /PID <pid> /F
```

### Response is "(DEMO) Echo: ..."
**Solution**: DEMO_MODE still enabled. Check .env file.

### Server starts but no response after 30s
**Solution**: Model loading timeout. Check CPU usage, available RAM.

---

## 📞 Reporting Issues

When reporting problems, include:

1. **Exact error message** from console/logs
2. **Steps to reproduce**
3. **Environment details** (Windows version, RAM, CPU)
4. **Server logs** (last 50 lines)
5. **Screenshot** if UI issue

**Log location**: Console output where uvicorn is running

**Example Issue Report**:
```
Issue: Test 3 fails with timeout

Steps:
1. Started server: python -m uvicorn app:app --host 127.0.0.1 --port 8000
2. Ran: python test_local_model.py
3. Waited 60 seconds, got timeout error

Environment:
- Windows 11
- 16GB RAM
- Intel i7-9700K
- Python 3.11.9

Server logs show:
[INFO] Loading tinyllama from ./models/tinyllama/...
[then nothing for 60s]

Screenshot: [attached]
```

---

## ✅ Ready for Installer Build When:

- [ ] 5/5 testers pass all Must Pass criteria
- [ ] No critical bugs found in 24 hours
- [ ] Average response time < 25 seconds
- [ ] Zero crashes in 50 consecutive requests
- [ ] Documentation complete

---

**Happy Testing! 🚀**
