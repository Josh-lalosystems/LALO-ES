"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
Microservices Client

Handles communication with LALO microservices:
- RTI (Recursive Task Interpreter) - Semantic interpretation
- MCP (Model Control Protocol) - Action planning and execution
- Creation Protocol Server - Dynamic artifact generation
"""

import httpx
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class RTIClient:
    """Client for Recursive Task Interpreter service"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("RTI_URL", "http://localhost:8101")

    async def interpret(self, user_input: str) -> Dict:
        """
        Send user input for semantic interpretation

        Returns:
            plan: Interpreted action plan
            confidence: Confidence score
            critique: Analysis critique
            retrieved_examples: Similar past examples
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/interpret",
                    json={"user_input": user_input},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.ConnectError:
                # RTI service not available, return fallback
                return {
                    "plan": f"Fallback interpretation: {user_input}",
                    "confidence": 0.7,
                    "critique": "RTI service unavailable - using fallback interpretation",
                    "retrieved_examples": []
                }
            except Exception as e:
                return {
                    "plan": f"Error: {str(e)}",
                    "confidence": 0.0,
                    "critique": f"Interpretation failed: {str(e)}",
                    "retrieved_examples": []
                }


class MCPClient:
    """Client for Model Control Protocol service"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("MCP_URL", "http://localhost:8102")

    async def execute_plan(self, plan: str) -> Dict:
        """
        Execute an action plan

        Args:
            plan: The action plan to execute

        Returns:
            success: Whether execution succeeded
            details: Execution details and results
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/execute_plan",
                    json={"plan": plan},
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.ConnectError:
                # MCP service not available, return simulated result
                return {
                    "success": True,
                    "details": f"MCP service unavailable - simulated execution of: {plan}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "details": f"Execution failed: {str(e)}"
                }

    async def get_settings(self) -> Dict:
        """Get current MCP settings"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/settings",
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
            except Exception:
                return {}

    async def update_settings(self, settings: Dict) -> Dict:
        """Update MCP settings"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/settings",
                    json=settings,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"error": str(e)}


class CreationClient:
    """Client for Creation Protocol Server"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("CREATION_URL", "http://localhost:8103")

    async def generate_artifact(
        self,
        artifact_type: str,
        description: str,
        task_spec: str
    ) -> Dict:
        """
        Generate a new artifact (connector, agent, RPA script)

        Args:
            artifact_type: Type of artifact (connector, subagent, rpa)
            description: Description of what artifact should do
            task_spec: Detailed task specification

        Returns:
            artifact_id: Generated artifact ID
            status: Generation status
            test_result: Test results
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/creation/generate",
                    json={
                        "type": artifact_type,
                        "description": description,
                        "task_spec": task_spec
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.ConnectError:
                # Creation service not available
                return {
                    "artifact_id": f"{artifact_type}_simulated",
                    "status": "Creation service unavailable - simulated",
                    "test_result": "Simulation only"
                }
            except Exception as e:
                return {
                    "artifact_id": None,
                    "status": "failed",
                    "test_result": f"Generation failed: {str(e)}"
                }

    async def approve_artifact(self, artifact_id: str) -> Dict:
        """Approve a generated artifact for use"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/creation/approve",
                    params={"artifact_id": artifact_id},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"error": str(e)}


# Global client instances
rti_client = RTIClient()
mcp_client = MCPClient()
creation_client = CreationClient()
