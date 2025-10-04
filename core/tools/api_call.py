# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
API Call Tool

Executes HTTP requests with retry, timeout and basic auth support.
"""
from __future__ import annotations
import httpx
from typing import Any, Dict, Optional
from core.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolExecutionResult

TIMEOUT = 20.0
RETRIES = 2

class APICallTool(BaseTool):
    @property
    def tool_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="api_call",
            description="Make HTTP requests to external APIs with retry and timeout",
            category="network",
            parameters=[
                ToolParameter(name="method", type="string", description="HTTP method", required=True, enum=["GET","POST","PUT","PATCH","DELETE"]),
                ToolParameter(name="url", type="string", description="URL to request", required=True),
                ToolParameter(name="headers", type="object", description="Request headers", required=False),
                ToolParameter(name="params", type="object", description="Query params", required=False),
                ToolParameter(name="json", type="object", description="JSON body", required=False),
            ],
            returns={"status": "HTTP status code", "headers": "Response headers", "json": "Parsed JSON if any", "text": "Raw text"},
            requires_approval=False,
        )

    async def execute(self, **kwargs) -> ToolExecutionResult:
        method = kwargs.get("method")
        url = kwargs.get("url")
        headers = kwargs.get("headers") or {}
        params = kwargs.get("params") or {}
        json_body = kwargs.get("json")

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
                last_exc = None
                for attempt in range(RETRIES + 1):
                    try:
                        resp = await client.request(method, url, headers=headers, params=params, json=json_body)
                        data = None
                        try:
                            data = resp.json()
                        except Exception:
                            pass
                        return ToolExecutionResult(
                            success=resp.status_code < 400,
                            output={
                                "status": resp.status_code,
                                "headers": dict(resp.headers),
                                "json": data,
                                "text": None if data is not None else resp.text,
                            },
                            error=None if resp.status_code < 400 else f"HTTP {resp.status_code}"
                        )
                    except Exception as e:
                        last_exc = e
                return ToolExecutionResult(success=False, error=str(last_exc))
        except Exception as e:
            return ToolExecutionResult(success=False, error=str(e))


api_call_tool = APICallTool()
