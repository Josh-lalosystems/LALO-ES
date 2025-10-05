# Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of LALO AI Platform and is protected by copyright law.
# Unauthorized copying, modification, distribution, or use of this software,
# via any medium, is strictly prohibited without the express written permission
# of LALO AI SYSTEMS, LLC.
#

# LALO Full Integration Plan - Current Status & Next Steps

## ✅ What's Been Completed (Phase 1)

### Core Workflow Infrastructure
1. **ConfidenceSystem** - Modernized to use your AI service
   - File: `confidence_system.py`
   - Uses GPT-3.5-turbo for interpretation
   - Uses Claude Haiku for confidence scoring
   - Returns structured results with reasoning

2. **WorkflowSession Database Model**
   - File: `core/database.py` (lines 110-169)
   - Tracks all 5 LALO workflow steps
   - Stores interpretation, planning, execution, review data
   - Permanent memory commit flag

3. **Workflow API Endpoints**
   - File: `core/routes/workflow_routes.py`
   - POST `/api/workflow/start` - Start with interpretation
   - GET `/api/workflow/{session_id}/status` - Get state
   - POST `/api/workflow/{session_id}/feedback` - User feedback
   - POST `/api/workflow/{session_id}/advance` - Next step
   - GET `/api/workflow/sessions` - List sessions

4. **Microservices Client**
   - File: `core/services/microservices_client.py`
   - RTI Client - Semantic interpretation
   - MCP Client - Plan execution
   - Creation Client - Artifact generation
   - All with fallback for when services are offline

## 🔧 Integration Steps Needed

### Step 1: Start Microservices

You need to start your three microservices in separate terminals:

```bash
# Terminal 1 - RTI Service
cd rtinterpreter
python -m uvicorn main:app --port 8101

# Terminal 2 - MCP Service
cd mcp
python -m uvicorn main:app --port 8102

# Terminal 3 - Creation Service
cd creation
python -m uvicorn main:app --port 8103
```

### Step 2: Update Workflow Routes to Use Microservices

Edit `core/routes/workflow_routes.py` and add at top:
```python
from ..services.microservices_client import rti_client, mcp_client, creation_client
```

Then update the `advance_workflow` function's planning section (around line 294):

```python
elif current_state == WorkflowState.PLANNING:
    if session.plan_approved != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot advance: plan not approved"
        )

    # Use MCP to generate action plan
    rti_result = await rti_client.interpret(session.interpreted_intent)
    session.action_plan = {
        "plan": rti_result["plan"],
        "confidence": rti_result["confidence"],
        "steps": rti_result.get("plan", "").split("\n"),
        "requires_backup": True
    }
    session.plan_confidence_score = rti_result["confidence"]

    # Move to backup verification
    session.current_state = WorkflowState.BACKUP_VERIFY
```

And update execution section (around line 305):

```python
elif current_state == WorkflowState.EXECUTING:
    # Use MCP to execute the plan
    execution_result = await mcp_client.execute_plan(session.action_plan["plan"])

    session.execution_results = {
        "success": execution_result["success"],
        "details": execution_result["details"],
        "timestamp": datetime.now().isoformat()
    }
    session.execution_success = 1 if execution_result["success"] else 0
    session.execution_steps_log = [execution_result["details"]]

    # Move to review
    session.current_state = WorkflowState.REVIEWING
```

### Step 3: Fix Import Issues in Advanced Systems

Your self-improvement, self-analysis, and sandbox systems have circular import issues. Create a service locator:

**Create `core/services/service_locator.py`:**
```python
"""
Service Locator Pattern
Resolves circular dependencies between services
"""

class ServiceLocator:
    _services = {}

    @classmethod
    def register(cls, name: str, service):
        cls._services[name] = service

    @classmethod
    def get(cls, name: str):
        return cls._services.get(name)

# Global instance
locator = ServiceLocator()
```

Then update imports in:
- `self_improvement_system.py`
- `self_analysis_system.py`
- `sandbox_manager.py`

Change from:
```python
from .audit_logger import AuditLogger
from .enhanced_memory_manager import EnhancedMemoryManager
```

To:
```python
from core.services.service_locator import locator

# Get services when needed
audit = locator.get("audit_logger")
memory = locator.get("memory_manager")
```

### Step 4: Create Service Initialization

**Create `core/services/__init__.py`:**
```python
"""
Initialize all LALO services
"""

from .service_locator import locator
from .ai_service import ai_service
from .key_management import key_manager
from .database_service import database_service
from .microservices_client import rti_client, mcp_client, creation_client

# Register services
locator.register("ai_service", ai_service)
locator.register("key_manager", key_manager)
locator.register("database_service", database_service)
locator.register("rti_client", rti_client)
locator.register("mcp_client", mcp_client)
locator.register("creation_client", creation_client)

__all__ = [
    "ai_service",
    "key_manager",
    "database_service",
    "rti_client",
    "mcp_client",
    "creation_client",
    "locator"
]
```

### Step 5: Frontend Chat Interface

**Create `lalo-frontend/src/components/WorkflowChat.tsx`:**

```typescript
import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  LinearProgress,
  Chip,
  Alert,
  Card,
  CardContent,
  CardActions,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

interface WorkflowState {
  session_id: string;
  current_state: string;
  original_request: string;
  interpreted_intent?: string;
  confidence_score?: number;
  reasoning_trace?: string[];
  suggested_clarifications?: string[];
  action_plan?: any;
  execution_results?: any;
}

export default function WorkflowChat() {
  const [request, setRequest] = useState('');
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startWorkflow = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/workflow/start', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_request: request })
      });

      if (!response.ok) throw new Error('Failed to start workflow');

      const data = await response.json();
      setWorkflow(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const submitFeedback = async (feedbackType: string) => {
    if (!workflow) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/workflow/${workflow.session_id}/feedback`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ feedback_type: feedbackType })
      });

      if (!response.ok) throw new Error('Failed to submit feedback');

      const data = await response.json();
      setWorkflow(data);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const advanceWorkflow = async () => {
    if (!workflow) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/workflow/${workflow.session_id}/advance`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to advance workflow');

      const data = await response.json();
      setWorkflow(data);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'interpreting': return 'primary';
      case 'planning': return 'info';
      case 'executing': return 'warning';
      case 'reviewing': return 'secondary';
      case 'completed': return 'success';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ maxWidth: 900, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        LALO Workflow
      </Typography>

      {/* Input */}
      {!workflow && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="What would you like LALO to do?"
            value={request}
            onChange={(e) => setRequest(e.target.value)}
            disabled={loading}
          />
          <Button
            variant="contained"
            onClick={startWorkflow}
            disabled={!request || loading}
            sx={{ mt: 2 }}
            endIcon={<SendIcon />}
          >
            Start Workflow
          </Button>
        </Paper>
      )}

      {/* Workflow Progress */}
      {workflow && (
        <Box>
          {/* Current State */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ flexGrow: 1 }}>
                  Current Step: {workflow.current_state}
                </Typography>
                <Chip
                  label={workflow.current_state}
                  color={getStateColor(workflow.current_state)}
                />
              </Box>

              {/* Step 1: Interpretation */}
              {workflow.current_state === 'interpreting' && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    <strong>Semantic Interpretation</strong>
                  </Typography>

                  {workflow.interpreted_intent && (
                    <>
                      <Alert severity="info" sx={{ mb: 2 }}>
                        {workflow.interpreted_intent}
                      </Alert>

                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Confidence: {((workflow.confidence_score || 0) * 100).toFixed(0)}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={(workflow.confidence_score || 0) * 100}
                        sx={{ mb: 2 }}
                      />

                      {workflow.reasoning_trace && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Reasoning:
                          </Typography>
                          <List dense>
                            {workflow.reasoning_trace.map((reason, idx) => (
                              <ListItem key={idx}>
                                <ListItemText primary={`${idx + 1}. ${reason}`} />
                              </ListItem>
                            ))}
                          </List>
                        </Box>
                      )}

                      {workflow.suggested_clarifications && workflow.suggested_clarifications.length > 0 && (
                        <Alert severity="warning" sx={{ mb: 2 }}>
                          <Typography variant="subtitle2">Suggested Clarifications:</Typography>
                          <List dense>
                            {workflow.suggested_clarifications.map((q, idx) => (
                              <ListItem key={idx}>
                                <ListItemText primary={q} />
                              </ListItem>
                            ))}
                          </List>
                        </Alert>
                      )}
                    </>
                  )}
                </Box>
              )}

              {/* Step 2: Planning */}
              {workflow.current_state === 'planning' && workflow.action_plan && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    <strong>Action Plan</strong>
                  </Typography>
                  <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
                    {JSON.stringify(workflow.action_plan, null, 2)}
                  </pre>
                </Box>
              )}

              {/* Step 3/4: Execution & Results */}
              {(workflow.current_state === 'executing' || workflow.current_state === 'reviewing') && workflow.execution_results && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    <strong>Execution Results</strong>
                  </Typography>
                  <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
                    {JSON.stringify(workflow.execution_results, null, 2)}
                  </pre>
                </Box>
              )}
            </CardContent>

            {/* Actions */}
            <CardActions>
              {workflow.current_state === 'interpreting' && (
                <>
                  <Button onClick={() => submitFeedback('approve')} variant="contained" color="success">
                    Approve
                  </Button>
                  <Button onClick={() => submitFeedback('reject')} variant="outlined" color="error">
                    Reject
                  </Button>
                  <Button onClick={() => submitFeedback('clarify')} variant="outlined">
                    Request Clarification
                  </Button>
                </>
              )}

              {workflow.current_state !== 'completed' && workflow.current_state !== 'error' && (
                <Button onClick={advanceWorkflow} variant="contained">
                  Continue
                </Button>
              )}

              {workflow.current_state === 'completed' && (
                <Button onClick={() => setWorkflow(null)} variant="contained" color="success">
                  Start New Workflow
                </Button>
              )}
            </CardActions>
          </Card>
        </Box>
      )}

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && <LinearProgress />}
    </Box>
  );
}
```

Add route in `lalo-frontend/src/App.tsx`:
```typescript
import WorkflowChat from './components/WorkflowChat';

// In your routes:
<Route path="/workflow" element={<WorkflowChat />} />
```

## Testing Complete Integration

1. **Start all services:**
   ```bash
   # Terminal 1 - Main app
   python app.py

   # Terminal 2 - RTI
   cd rtinterpreter && python -m uvicorn main:app --port 8101

   # Terminal 3 - MCP
   cd mcp && python -m uvicorn main:app --port 8102

   # Terminal 4 - Creation
   cd creation && python -m uvicorn main:app --port 8103
   ```

2. **Add API keys** via Settings page

3. **Test workflow:**
   - Go to `/workflow` in frontend
   - Enter: "Analyze my sales data and create a report"
   - Watch 5-step process
   - Approve/reject at each step

## Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API | ✅ Working | All endpoints created |
| Database | ✅ Working | WorkflowSession table ready |
| Confidence System | ✅ Working | Using real AI models |
| Microservices Client | ✅ Created | With fallbacks |
| Workflow Routes | ⚠️ Needs update | Add microservice calls |
| RTI Integration | ⏳ Pending | Service runs, needs wiring |
| MCP Integration | ⏳ Pending | Service runs, needs wiring |
| Creation Integration | ⏳ Pending | Service runs, needs wiring |
| Frontend Chat UI | ⏳ Pending | Component ready to add |
| Self-Improvement | ⏳ Pending | Fix imports |
| Self-Analysis | ⏳ Pending | Fix imports |
| Sandbox Manager | ⏳ Pending | Fix imports |

## Estimated Time to Complete

- Microservices integration: 1 hour
- Frontend implementation: 1-2 hours
- Self-improvement fixes: 30 minutes
- Testing & debugging: 1 hour

**Total: 3.5-4.5 hours to full functionality**

## Next Immediate Actions

1. Start the three microservices
2. Update workflow routes with microservice calls
3. Test backend workflow with Postman/curl
4. Add frontend component
5. Test end-to-end with real request

Everything is architected and ready - just needs the final wiring!
