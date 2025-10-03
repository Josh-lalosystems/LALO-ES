
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional

from .workflow_coordinator import WorkflowCoordinator, WorkflowState
from .confidence_system import ConfidenceSystem
from .enhanced_memory_manager import EnhancedMemoryManager

app = FastAPI()

# Initialize components
workflow_coordinator = WorkflowCoordinator()

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
    stage: WorkflowState

@app.post("/workflow/start")
async def start_workflow(request: UserRequest):
    """
    Initiates a new workflow from user request
    """
    try:
        session_id, context = await workflow_coordinator.start_workflow(request.message)
        
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
        context = await workflow_coordinator.process_feedback(
            session_id,
            feedback_request.feedback,
            feedback_request.stage
        )
        
        # Advance workflow in background if no clarification needed
        background_tasks.add_task(workflow_coordinator.advance_workflow, session_id)
        
        return {
            "session_id": session_id,
            "state": context.current_state.value,
            "requires_feedback": context.current_state != WorkflowState.COMPLETED,
            "next_steps": _get_next_steps(context)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _get_next_steps(context) -> Dict:
    """
    Determines next steps based on workflow context
    """
    if context.current_state == WorkflowState.INTERPRETING:
        return {
            "action": "clarify",
            "points": context.interpretation.suggested_clarifications
        }
    elif context.current_state == WorkflowState.PLANNING:
        return {
            "action": "review_plan",
            "plan": context.plan
        }
    elif context.current_state == WorkflowState.EXECUTING:
        return {
            "action": "monitor_execution",
            "progress": context.execution_results
        }
    elif context.current_state == WorkflowState.REVIEWING:
        return {
            "action": "final_review",
            "results": context.execution_results
        }
    return {"action": "complete"}
def add_document_api(req: AddDocRequest):
    # Generate embedding using OpenAI
    if not api_keys["openai"]:
        raise HTTPException(status_code=400, detail="OpenAI API key not set")
    client = openai.OpenAI(api_key=api_keys["openai"])
    emb_response = client.embeddings.create(
        input=req.text,
        model="text-embedding-3-small"  # or another embedding model
    )
    embedding = emb_response.data[0].embedding
    collection.add(
        ids=[req.doc_id],
        documents=[req.text],
        embeddings=[embedding]
    )
    return {"status": "success"}

class QueryRequest(BaseModel):
    query: str
    n_results: int = 3

@app.post("/semantic_search")
def semantic_search_api(req: QueryRequest):
    # Generate embedding for query
    if not api_keys["openai"]:
        raise HTTPException(status_code=400, detail="OpenAI API key not set")
    client = openai.OpenAI(api_key=api_keys["openai"])
    emb_response = client.embeddings.create(
        input=req.query,
        model="text-embedding-3-small"
    )
    query_embedding = emb_response.data[0].embedding
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=req.n_results
    )
    return results
def get_keys():
    return {
        "openai_set": api_keys["openai"] is not None,
        "anthropic_set": api_keys["anthropic"] is not None
    }

@app.post("/list_onedrive_files")
def list_onedrive_files(auth: AuthRequest):
    try:
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
