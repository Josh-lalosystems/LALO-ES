"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""


from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import openai
import anthropic

# Defer importing internal modules that perform package-relative imports.
# Import them lazily inside endpoints to avoid "attempted relative import"
# errors when uvicorn's reloader imports this module at startup.

# We'll instantiate the WorkflowCoordinator lazily on first use.
workflow_coordinator = None


def get_workflow_coordinator():
    """Lazily instantiate the WorkflowCoordinator to avoid importing
    many internal modules at top-level (which breaks uvicorn reload).
    """
    global workflow_coordinator
    if workflow_coordinator is None:
        from workflow_coordinator import WorkflowCoordinator
        workflow_coordinator = WorkflowCoordinator()
    return workflow_coordinator


app = FastAPI()


# API Keys storage
api_keys = {
    "openai": None,
    "anthropic": None
}

# Note: workflow_coordinator will be initialized lazily via get_workflow_coordinator()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only; restrict in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserRequest(BaseModel):
    message: str
    context: Optional[Dict] = None

class FeedbackRequest(BaseModel):
    feedback: Dict
    # stage is passed as a string (enum name) to avoid importing WorkflowState
    stage: Optional[str] = None

class AuthRequest(BaseModel):
    client_id: str
    tenant_id: str

class ChatRequest(BaseModel):
    message: str
    provider: str
    model: Optional[str] = None
    # stage represented as simple string to avoid importing WorkflowState at module import
    stage: Optional[str] = None

@app.post("/workflow/start")
async def start_workflow(request: UserRequest):
    """
    Initiates a new workflow from user request
    """
    try:
        coordinator = get_workflow_coordinator()
        session_id, context = await coordinator.start_workflow(request.message)
        
        return {
            "session_id": session_id,
            "state": context.current_state.value,
            "interpretation": context.interpretation.__dict__ if context.interpretation else None,
            "requires_feedback": context.interpretation.feedback_required if context.interpretation else True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflow/{session_id}/feedback")
async def provide_feedback(
    session_id: str,
    feedback_request: FeedbackRequest,
    background_tasks: BackgroundTasks
):
    """
    Processes user feedback for current workflow stage
    """
    try:
        coordinator = get_workflow_coordinator()

        # Convert stage string (if provided) to WorkflowState inside coordinator context
        stage_value = None
        if feedback_request.stage:
            from workflow_coordinator import WorkflowState
            try:
                # Allow either name or value
                if feedback_request.stage.upper() in WorkflowState.__members__:
                    stage_value = WorkflowState[feedback_request.stage.upper()]
                else:
                    # Match by value
                    for s in WorkflowState:
                        if s.value == feedback_request.stage:
                            stage_value = s
                            break
            except Exception:
                stage_value = None

        context = await coordinator.process_feedback(
            session_id,
            feedback_request.feedback,
            stage_value
        )

        # Advance workflow in background if no clarification needed
        background_tasks.add_task(coordinator.advance_workflow, session_id)

        return {
            "session_id": session_id,
            "state": context.current_state.value,
            "requires_feedback": context.current_state.value != "completed",
            "next_steps": _get_next_steps(context)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _get_next_steps(context) -> Dict:
    """
    Determines next steps based on workflow context
    """
    # Normalize current_state to a string value without importing WorkflowState
    state_val = getattr(context.current_state, 'value', context.current_state)
    if state_val == "interpreting":
        return {
            "action": "clarify",
            "points": context.interpretation.suggested_clarifications
        }
    elif state_val == "planning":
        return {
            "action": "review_plan",
            "plan": context.plan
        }
    elif state_val == "executing":
        return {
            "action": "monitor_execution",
            "progress": context.execution_results
        }
    elif state_val == "reviewing":
        return {
            "action": "final_review",
            "results": context.execution_results
        }
    return {"action": "complete"}

@app.post("/list_onedrive_files")
def list_onedrive_files(auth: AuthRequest):
    try:
        # Lazy import to avoid top-level package-relative imports
        from tool_connector_ui import UiToolConnector
        connector = UiToolConnector(auth.client_id, auth.tenant_id)
        result = connector.execute("list_onedrive_files", {})
        return result.summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat_inference(req: ChatRequest):
    try:
        if req.provider == "openai":
            if not api_keys["openai"]:
                raise HTTPException(status_code=400, detail="OpenAI API key not set")
            client = openai.OpenAI(api_key=api_keys["openai"])
            response = client.chat.completions.create(
                model=req.model,
                messages=[{"role": "user", "content": req.message}]
            )
            return {"response": response.choices[0].message.content}
        elif req.provider == "anthropic":
            if not api_keys["anthropic"]:
                raise HTTPException(status_code=400, detail="Anthropic API key not set")
            client = anthropic.Anthropic(api_key=api_keys["anthropic"])
            response = client.messages.create(
                model=req.model,
                max_tokens=512,
                messages=[{"role": "user", "content": req.message}]
            )
            return {"response": response.content}
        else:
            raise HTTPException(status_code=400, detail="Unknown provider")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
