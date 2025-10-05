# Frontend Critical Fixes Required

**Status**: Pre-Installer Blockers
**Priority**: CRITICAL - Must fix before Windows installer build
**Date**: 2025-10-05

---

## Critical Issues Identified

### 1. **Authentication UI - "Get Demo Token" Still Visible** ❌
**Problem**: DevLogin.tsx still shows "Get Demo Token" button instead of proper login interface

**Current State**:
```tsx
// lalo-frontend/src/components/DevLogin.tsx
<Button variant="contained" onClick={handleDevLogin}>
  {loading ? <CircularProgress size={20} /> : 'Get Demo Token'}
</Button>
```

**Required Fix**:
- Replace with proper username/password login form
- Call `/auth/login` endpoint (already exists in apiClient)
- Store JWT token on successful login
- Redirect to `/lalo` (unified interface)

**Files to Modify**:
- `lalo-frontend/src/components/DevLogin.tsx` → Rename to `Login.tsx`
- `lalo-frontend/src/App.tsx` → Update import

---

### 2. **Session Expired Error on Request Submission** ❌
**Problem**: Clicking "Submit Request" shows "Session Expired" popup

**Root Cause Analysis**:
- `UnifiedLALO.tsx` line 239: `catch (err: any)` catches auth errors
- `apiClient.ts` line 38-47: Returns 401/403 and throws "Unauthorized" error
- Frontend interprets this as "session expired" even when it's actually a missing API key or other issue

**Current Error Flow**:
1. User submits request → `/api/ai/chat`
2. Backend returns 401 (no API keys configured OR invalid token)
3. apiClient removes token and throws error
4. UnifiedLALO displays: "Unauthorized" → Interpreted as "Session Expired"

**Required Fix**:
```typescript
// lalo-frontend/src/components/user/UnifiedLALO.tsx (line 239-245)
catch (err: any) {
  // Distinguish between auth errors and other errors
  if (err.status === 401 || err.status === 403) {
    if (err.message?.includes('API key') || err.message?.includes('keys')) {
      setError('No API keys configured. Please add API keys in Settings.');
    } else {
      setError('Session expired. Please log in again.');
      // Redirect to login after 2 seconds
      setTimeout(() => window.location.href = '/login', 2000);
    }
  } else {
    setError(err.message || 'Failed to process request');
  }
  console.error('Request failed:', err);
}
```

---

### 3. **Chat and Image Generation Still Separate** ❌
**Problem**: `/request` (RequestForm) and `/images` (ImageGenerator) are separate routes

**Current State**:
- App.tsx line 49-50: Two separate routes
- User must navigate between pages for different modes

**Required Fix**:
- Make `/lalo` (UnifiedLALO) the PRIMARY interface (already done in routing)
- Remove `/request` and `/images` routes OR redirect to `/lalo`
- UnifiedLALO already has chat/image toggle (line 259-262) ✓

**Files to Modify**:
```tsx
// lalo-frontend/src/App.tsx
// REMOVE or REDIRECT these routes:
<Route path="/request" element={<Navigate to="/lalo" replace />} />
<Route path="/images" element={<Navigate to="/lalo" replace />} />
```

**Navigation Updates**:
- Update Navigation.tsx to remove separate "Request" and "Images" links
- Keep only "LALO AI" link to unified interface

---

### 4. **Tools Section Broken** ❌
**Problem**: Tools section entirely non-functional

**Current State**:
- UnifiedLALO.tsx lines 86-93: Hardcoded tool list with frontend-only state
- Tools are toggled but never sent to backend
- No actual tool execution happens

**Required Implementation**:

#### Backend (Already Exists):
- `/api/admin/tools` - List available tools ✓
- `/api/admin/tools/{tool}/enable` - Enable tool ✓
- `/api/admin/tools/{tool}/disable` - Disable tool ✓

#### Frontend Fix:
```tsx
// lalo-frontend/src/components/user/UnifiedLALO.tsx

// Fetch tools from backend on mount
useEffect(() => {
  const fetchTools = async () => {
    try {
      const backendTools = await adminAPI.listTools();
      setTools(backendTools.map(t => ({
        name: t.name,
        enabled: t.enabled,
        icon: getToolIcon(t.category), // Map category to icon
        description: t.description
      })));
    } catch (err) {
      console.error('Failed to load tools:', err);
    }
  };
  fetchTools();
}, []);

// Send tool state to backend on toggle
const handleToolToggle = async (toolName: string) => {
  const tool = tools.find(t => t.name === toolName);
  try {
    if (tool?.enabled) {
      await adminAPI.disableTool(toolName);
    } else {
      await adminAPI.enableTool(toolName);
    }
    setTools(tools.map(t =>
      t.name === toolName ? { ...t, enabled: !t.enabled } : t
    ));
  } catch (err) {
    console.error('Failed to toggle tool:', err);
    setError('Failed to update tool settings');
  }
};

// Include enabled tools in request
const enabledTools = tools.filter(t => t.enabled).map(t => t.name);
await aiAPI.sendRequest({
  prompt: currentInput,
  model,
  tools: enabledTools, // ADD THIS
  max_tokens: 2000,
  temperature: 0.7,
});
```

---

### 5. **Missing Advanced Features in UI** ❌

#### A. **Self-Improvement Feedback System**
**Backend Exists**:
- `POST /api/ai/feedback` - Submit feedback ✓
- Stores in `feedback` table ✓

**Frontend Missing**:
- No feedback UI on responses
- No "Was this helpful?" buttons
- No feedback history view

**Required Component**: `lalo-frontend/src/components/user/FeedbackWidget.tsx`
```tsx
// Add to each message in UnifiedLALO
{msg.role === 'assistant' && (
  <FeedbackWidget responseId={response.id} />
)}
```

#### B. **Sandboxes**
**Backend Exists**:
- `core/services/sandbox.py` - Sandboxed code execution ✓
- Isolated Python environments ✓

**Frontend Missing**:
- No sandbox UI
- No code execution interface
- No output display

**Required Component**: `lalo-frontend/src/components/user/SandboxExecutor.tsx`

#### C. **Agent Pools / Specialized Agents**
**Backend Exists**:
- `core/services/router_model.py` - Routes to specialized agents ✓
- Agent marketplace API endpoints ✓

**Frontend Missing**:
- Agent pool visibility is hidden
- No way to see which agents are available
- No agent selection UI

**Required Enhancement**:
```tsx
// Add to UnifiedLALO
const [availableAgents, setAvailableAgents] = useState([]);

useEffect(() => {
  agentAPI.listAgents().then(setAvailableAgents);
}, []);

// Show agent selector when model === 'auto'
{model === 'auto' && (
  <Typography variant="caption">
    Router will select from: {availableAgents.map(a => a.name).join(', ')}
  </Typography>
)}
```

---

## Summary of Required Changes

### Files to Create:
1. `lalo-frontend/src/components/auth/Login.tsx` - Proper login form
2. `lalo-frontend/src/components/user/FeedbackWidget.tsx` - Feedback UI
3. `lalo-frontend/src/components/user/SandboxExecutor.tsx` - Sandbox UI
4. `lalo-frontend/src/components/shared/AgentSelector.tsx` - Agent visibility

### Files to Modify:
1. ✅ `lalo-frontend/src/App.tsx` - Update routing, remove separate request/image pages
2. ✅ `lalo-frontend/src/components/user/UnifiedLALO.tsx` - Fix tools, add agent visibility
3. ✅ `lalo-frontend/src/components/shared/Navigation.tsx` - Update nav links
4. ✅ `lalo-frontend/src/services/apiClient.ts` - Better error messages

### Backend API Updates:
- ✅ Verify `/api/ai/chat` accepts `tools` parameter
- ✅ Ensure proper error messages for missing API keys vs auth failures

---

## Testing Checklist

After fixes, verify:
- [ ] Login with username/password works
- [ ] Token is stored and persists across page refreshes
- [ ] Submitting request without API keys shows clear error (not "session expired")
- [ ] Chat and image generation work in unified interface
- [ ] Tools can be enabled/disabled and are sent to backend
- [ ] Feedback buttons appear on AI responses
- [ ] Agent routing information is visible
- [ ] No "Get Demo Token" button visible in production build

---

## Implementation Order

**Phase 1: Critical Fixes (1-2 hours)**
1. Fix Login UI (remove demo token)
2. Fix "Session Expired" error handling
3. Unify request/image routes

**Phase 2: Tool Functionality (1 hour)**
4. Connect tools to backend
5. Implement tool toggle persistence

**Phase 3: Advanced Features (2-3 hours)**
6. Add feedback widget
7. Add sandbox executor
8. Add agent visibility

**Phase 4: Testing (1 hour)**
9. End-to-end testing of all flows
10. Production build verification

**Total Estimated Time**: 5-7 hours

---

## Notes

- UnifiedLALO.tsx is actually quite well-built - it just needs proper backend integration
- Most backend functionality already exists - primarily a frontend integration issue
- Authentication is the critical blocker - fix this first
- Tools and advanced features can be added incrementally after core flow works
