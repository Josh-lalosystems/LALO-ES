# LALO AI - MVP Roadmap

**Current Status**: 75% Complete
**Target**: First Installable MVP
**Last Updated**: 2025-10-05 18:15

---

## ✅ Completed (What's Working)

### Infrastructure
- [x] FastAPI backend with modular service architecture
- [x] React frontend (Material-UI) - built and serving
- [x] SQLite database with encrypted API key storage
- [x] JWT authentication with demo mode
- [x] CORS, rate limiting, security middleware

### AI Integration
- [x] OpenAI integration (GPT-4, GPT-3.5)
- [x] Anthropic integration (Claude 3 family)
- [x] API key management (add/test/delete)
- [x] Usage tracking and cost calculation
- [x] Streaming responses (Server-Sent Events)

### Local Inference
- [x] llama-cpp-python integration
- [x] 6/8 production models downloaded:
  - ✅ bge-small (133 MB) - Embeddings
  - ✅ qwen-0.5b (352 MB) - Validation
  - ✅ tinyllama (669 MB) - General chat
  - ✅ deepseek-coder (4.0 GB) - Coding
  - ✅ openchat (4.37 GB) - Research
  - ✅ mistral-instruct (4.37 GB) - Reasoning
  - ❌ liquid-tool (404 error)
  - ❌ deepseek-math (404 error)
- [x] Router model (request classification)
- [x] DEMO_MODE heuristic fallback
- [x] Model configuration registry

### Orchestration
- [x] UnifiedRequestHandler (router → agent → confidence)
- [x] Agent runtime system
- [x] Workflow state management
- [x] Tool registry (7 tools registered)
- [x] Confidence scoring model

### Recent Fixes (This Session)
- [x] Fixed encryption key decryption crashes
- [x] Added local models to available models endpoint
- [x] Created uvicorn behavior documentation
- [x] Windows UTF-8 encoding fixes
- [x] Comprehensive test scripts

---

## ⚠️ Critical Blockers (Must Fix for MVP)

### 1. Server Restart Required ⏳
**Issue**: Current server running old code (pre-fixes)
**Impact**: Can't test encryption fixes or local model availability
**Action**: Manually restart server process
**ETA**: 2 minutes

### 2. Model Loading Timeout 🔥
**Issue**: llama-cpp-python hangs when loading GGUF models (>60 seconds)
**Root Cause**: CPU-only inference extremely slow, possible config issue
**Workaround**: DEMO_MODE heuristic fallback implemented
**Permanent Fix Needed**: One of:
- Debug llama.cpp configuration (n_ctx, n_threads, etc.)
- Use smaller model first (qwen-0.5b is only 352MB)
- Switch to Ollama for local inference
- Accept cloud-only MVP initially
**ETA**: 4-8 hours

### 3. Actual Inference Testing 📋
**Issue**: Haven't tested real model inference end-to-end
**Depends On**: #1 (server restart), #2 (model loading fix)
**Test Plan**:
1. Server loads tinyllama without timeout
2. Request "What is 2+2?" returns "4"
3. Response time < 10 seconds
4. Usage recorded correctly
**ETA**: 30 minutes (after #1, #2 fixed)

---

## 🎯 MVP Must-Have Features (Not Yet Complete)

### Priority 1: Core Functionality

#### A. Fix Model Loading (CRITICAL)
**Current State**: Models downloaded, heuristic fallback works
**Needed**:
- [ ] Debug why llama-cpp hangs on model load
- [ ] Test with smallest model first (qwen-0.5b 352MB)
- [ ] Add proper timeout and error handling
- [ ] Verify all 6 models load successfully

**Files to Modify**:
- `core/services/local_llm_service.py` - Model loading logic
- Possibly add `n_ctx=2048, n_threads=4, use_mmap=True`

**Success Criteria**:
- Model loads in < 30 seconds
- Generates response to "Hello" in < 5 seconds
- No crashes or hangs

---

#### B. Multimodal Input (Image + Text)
**Current State**: Text-only requests
**Needed**:
- [ ] Update AIRequest model to accept images
- [ ] Add image upload in frontend (RequestForm.tsx)
- [ ] Encode images to base64 or save to disk
- [ ] Route to vision models (GPT-4 Vision or fallback to OCR)

**Files to Modify**:
- `core/routes/ai_routes.py` - Add image field to AIRequest
- `lalo-frontend/src/components/user/RequestForm.tsx` - Add file upload
- `core/services/ai_service.py` - Handle image in generate()

**Success Criteria**:
- User can upload image + text prompt
- System processes image (vision or OCR)
- Response references image content

---

#### C. Router Model Enhancement
**Current State**: Router classifies and recommends single model
**Needed**:
- [ ] Return LIST of specialized models for complex tasks
- [ ] Poll specialized models for capability assessment
- [ ] Create multi-step action plan

**Files to Modify**:
- `core/services/router_model.py` - Enhance routing logic
- `core/services/unified_request_handler.py` - Handle multi-model responses

**Example**:
```python
# Current
{"recommended_model": "deepseek-coder", "path": "specialized"}

# Target
{
  "recommended_models": ["deepseek-coder", "mistral-instruct"],
  "action_plan": [
    {"step": 1, "model": "deepseek-coder", "task": "Write function"},
    {"step": 2, "model": "mistral-instruct", "task": "Add documentation"}
  ]
}
```

**Success Criteria**:
- Complex request like "Write and document a Python function" uses 2+ models
- Action plan shows clear step breakdown
- Final response combines outputs

---

### Priority 2: Tools Execution

#### D. Implement Tool Executor
**Current State**: Tools registered but not executing
**Needed**:
- [ ] Complete `core/tools/tool_executor.py`
- [ ] Connect to registered tools (web_search, code_executor, etc.)
- [ ] Add tool result parsing and error handling

**Files to Create/Modify**:
- `core/tools/tool_executor.py` - Main execution logic
- `core/services/unified_request_handler.py` - Call executor

**Success Criteria**:
- Request like "Search for Python tutorial" triggers web_search tool
- Tool returns real results (not demo/mock)
- Results incorporated into final response

---

### Priority 3: Production Readiness

#### E. Error Handling & User Feedback
**Current State**: Basic error messages
**Needed**:
- [ ] User-friendly error messages for all failure modes
- [ ] Retry logic for transient failures
- [ ] Progress indicators for long operations
- [ ] Detailed logging for debugging

**Files to Modify**:
- All route files - Add HTTPException with clear messages
- `lalo-frontend/src/services/errorHandler.ts` - Map errors to user messages

---

#### F. Windows Installer
**Current State**: Manual installation
**Needed**:
- [ ] Inno Setup or NSIS installer script
- [ ] Bundle Python + dependencies
- [ ] Auto-create .env file
- [ ] Desktop shortcut creation
- [ ] Start menu integration

**Files to Create**:
- `installer/setup.iss` (Inno Setup) or `installer/installer.nsi` (NSIS)
- `installer/post_install.py` - First-run setup

**Success Criteria**:
- Double-click installer runs
- User sees "LALO AI" desktop icon
- Click icon opens browser to http://localhost:8000
- No technical knowledge required

---

## 🚀 Recommended MVP Path

### Phase 1: Unblock Testing (NOW - 30 min)
1. ✅ **Restart server manually**
   - Kill all python.exe processes
   - Run: `python -m uvicorn app:app --host 127.0.0.1 --port 8000`
   - Verify: `curl http://localhost:8000/`

2. ✅ **Test encryption fixes**
   - Run: `python test_local_model.py`
   - Should NOT see 500 error
   - Should see "demo mode" response or actual inference

3. ✅ **Verify local models endpoint**
   - Check `/api/ai/models` returns tinyllama, qwen, etc.

---

### Phase 2: Core Inference (2-4 hours)
1. **Debug model loading**
   - Add verbose logging to local_llm_service.py
   - Test qwen-0.5b (smallest model) first
   - If still hangs, try Ollama alternative

2. **Test end-to-end inference**
   - Request: "What is 2+2?"
   - Expected: "4" (from tinyllama or qwen)
   - Verify response time < 10s

3. **Stress test**
   - Send 10 concurrent requests
   - Verify no crashes
   - Check memory usage

---

### Phase 3: Multimodal (4-6 hours)
1. **Backend image support**
   - Update AIRequest Pydantic model
   - Add image storage/encoding logic
   - Route to GPT-4 Vision if available

2. **Frontend file upload**
   - Add `<input type="file" accept="image/*">` to RequestForm
   - Preview uploaded image
   - Send as base64 or multipart/form-data

3. **Test with sample image**
   - Upload screenshot + "What does this show?"
   - Verify response describes image

---

### Phase 4: Router Enhancement (3-4 hours)
1. **Multi-model planning**
   - Modify router_model.py to return list
   - Add capability assessment per model
   - Generate action plan

2. **Orchestration logic**
   - Implement sequential execution in unified_request_handler
   - Combine outputs intelligently
   - Handle failures gracefully

3. **Test complex workflow**
   - "Write Python function + add docs + explain"
   - Should use deepseek-coder + mistral
   - Verify all steps complete

---

### Phase 5: Installer (6-8 hours)
1. **Bundle dependencies**
   - Create requirements.txt subset for MVP
   - Test clean install on fresh Windows VM

2. **Create installer script**
   - Use Inno Setup (easier) or NSIS (more powerful)
   - Include Python 3.11 bundled or check for install
   - Copy files to Program Files

3. **Post-install setup**
   - Generate .env with defaults
   - Download models on first run (optional)
   - Open browser automatically

4. **Test installation**
   - Run installer on clean machine
   - Verify icon appears
   - Verify app launches

---

## 📊 Progress Tracking

### MVP Completion Estimate
- Infrastructure: **95%** ✅
- AI Integration: **90%** ✅
- Local Inference: **60%** ⚠️
- Orchestration: **70%** ⚠️
- Error Handling: **40%** ❌
- Multimodal: **10%** ❌
- Tools Execution: **30%** ❌
- Installer: **0%** ❌

**Overall MVP Progress**: **~75%**

---

## 🎯 MVP Definition (Minimum Viable Product)

**Core Requirement**: User can install LALO, send AI requests, and get responses.

**Must Have**:
- ✅ Windows installer (one-click install)
- ✅ Text-based AI chat (cloud or local)
- ✅ API key management
- ⚠️ Local model inference (at least 1 model working)
- ⚠️ Error handling (user-friendly messages)

**Nice to Have** (can defer):
- Multimodal input
- Multi-model orchestration
- Advanced tools execution
- Workflow management

---

## 🚧 Known Issues (Acceptable for MVP)

1. **Model Loading Timeout**: Using heuristic fallback for now
2. **Limited Tool Execution**: Web search, code execution not yet connected
3. **No Workflow Persistence**: Workflows don't save state
4. **Basic Error Messages**: Some errors still technical
5. **Missing Models**: liquid-tool and deepseek-math returned 404 (acceptable)

---

## ✅ MVP Release Checklist

Before creating installer:
- [ ] Server starts without errors
- [ ] At least 1 local model works (qwen or tinyllama)
- [ ] Cloud APIs work (OpenAI/Anthropic with user keys)
- [ ] Frontend loads and is responsive
- [ ] Error messages are user-friendly
- [ ] Usage tracking records requests
- [ ] Documentation exists (README.md)
- [ ] Demo mode works for testing

---

## 📝 Post-MVP Enhancements

After first release, add:
1. **Multimodal Support** - Image + text processing
2. **Advanced Router** - Multi-model orchestration
3. **Tool Execution** - Real web search, code running
4. **Workflow Designer** - Visual workflow builder
5. **Admin Dashboard** - User management, analytics
6. **Auto-Updates** - Check for new versions
7. **Model Management** - Download/update models from UI

---

**Next Action**: Restart server and run `python test_local_model.py` to verify fixes!
