# Copyright (c) 2025 LALO AI LLC. All rights reserved.

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
import os

app = FastAPI(title="LALO Core Runtime")

templates = Jinja2Templates(directory="templates")

RTI_URL = os.getenv("RTI_URL", "http://localhost:8101")
MCP_URL = os.getenv("MCP_URL", "http://localhost:8102")
CREATION_URL = os.getenv("CREATION_URL", "http://localhost:8103")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/interpret", response_class=HTMLResponse)
async def interpret(request: Request, user_input: str = Form(...)):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{RTI_URL}/interpret", json={"user_input": user_input})
        rti_response = r.json()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "rti_response": rti_response,
            "user_input": user_input
        }
    )

@app.post("/approve_plan", response_class=HTMLResponse)
async def approve_plan(request: Request, plan: str = Form(...)):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{MCP_URL}/execute_plan", json={"plan": plan})
        mcp_result = r.json()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "mcp_result": mcp_result
        }
    )
