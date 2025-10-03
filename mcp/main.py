# Copyright (c) 2025 LALO AI LLC. All rights reserved.

from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import random

from .chrome_client import check_frontend
from .settings import settings
from fastapi import HTTPException

app = FastAPI(title="Model Control Protocol (MCP) — Action Planner")

class PlanRequest(BaseModel):
    plan: str

class PlanResult(BaseModel):
    success: bool
    details: str

@app.post("/execute_plan", response_model=PlanResult)
async def execute_plan(req: PlanRequest):
    """
    Simulate executing a high-confidence action plan.
    After execution, perform a lightweight frontend check using Playwright.
    """
    # non-blocking sleep for demo
    await asyncio.sleep(0.5)

    # Simulate plan execution logic (placeholder)
    success = random.choice([True, True, True, False])  # mostly succeeds

    # Run a quick frontend check (best-effort, non-fatal)
    try:
        check = await check_frontend(settings.FRONTEND_URL, wait_selector=settings.FRONTEND_WAIT_SELECTOR, timeout=settings.FRONTEND_TIMEOUT, screenshot=False)
        frontend_status = check.get("status", "unknown")
        frontend_details = check.get("details")
    except Exception as e:
        frontend_status = "error"
        frontend_details = str(e)

    details = f"Executed plan: {req.plan}. frontend_check={frontend_status}"
    if frontend_details:
        details += f"; frontend_details={frontend_details}"

    return PlanResult(success=success, details=details)


class SettingsModel(BaseModel):
    frontend_url: str
    wait_selector: str | None = None
    timeout: int | None = None


@app.get("/settings")
async def get_settings():
    return {"frontend_url": settings.FRONTEND_URL, "wait_selector": settings.FRONTEND_WAIT_SELECTOR, "timeout": settings.FRONTEND_TIMEOUT}


@app.post("/settings")
async def update_settings(payload: SettingsModel):
    # Update in-memory settings; for persistence you can write to env or a config file
    if payload.frontend_url:
        settings.FRONTEND_URL = payload.frontend_url
    if payload.wait_selector is not None:
        settings.FRONTEND_WAIT_SELECTOR = payload.wait_selector
    if payload.timeout is not None:
        settings.FRONTEND_TIMEOUT = payload.timeout
    return {"ok": True, "frontend_url": settings.FRONTEND_URL}
