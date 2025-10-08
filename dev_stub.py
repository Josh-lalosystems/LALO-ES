"""
Lightweight development stub server.

Purpose:
- Serve frontend static build (if present) for quick integration testing.
- Provide minimal fake API endpoints used by the frontend so UI testing can continue
  while the full backend is debugged.

Usage:
  .\venv\Scripts\Activate.ps1
  python -m uvicorn dev_stub:app --host 127.0.0.1 --port 8000
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid

app = FastAPI(title="LALO Dev Stub")

# Serve built frontend if available
BUILD_DIR = os.path.join(os.path.dirname(__file__), 'lalo-frontend', 'build')
if os.path.isdir(BUILD_DIR):
    app.mount('/', StaticFiles(directory=BUILD_DIR, html=True), name='frontend')


class WorkflowRequest(BaseModel):
    message: str


class ChatRequest(BaseModel):
    message: str
    provider: str = 'local'
    model: str | None = None


@app.post('/workflow/start')
async def start_workflow(req: WorkflowRequest):
    # Return a fake session id and basic context
    session_id = str(uuid.uuid4())
    return {
        'session_id': session_id,
        'state': 'interpreting',
        'interpretation': None,
        'requires_feedback': False,
    }


@app.post('/chat')
async def chat(req: ChatRequest):
    # Simple echo / canned response for UI testing
    if not req.message:
        raise HTTPException(status_code=400, detail='No message')
    return {'response': f"[dev-stub] Echo: {req.message[:200]}"}


@app.get('/health')
async def health():
    return {'status': 'ok'}
