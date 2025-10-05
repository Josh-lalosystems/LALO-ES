"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
Unified Request Handler - Main entry point for all AI requests

Orchestrates the complete request flow:
Router → Simple/Complex Path → Confidence → Response

This is the "brain" of LALO that coordinates all Phase 1 & 2 components.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from core.services.router_model import router_model
from core.services.agent_orchestrator import agent_orchestrator
from core.services.local_llm_service import local_llm_service

logger = logging.getLogger(__name__)


class UnifiedRequestHandler:
    """
    Main entry point for all user requests

    Request Flow:
    1. RouterModel classifies request (simple/complex/specialized)
    2. Route to appropriate path:
       - Simple: Direct LLM call
       - Complex: AgentOrchestrator multi-step workflow
       - Specialized: Specific model/tool
    3. ConfidenceModel validates output
    4. Return response with metadata

    This replaces the old fixed workflow with intelligent routing.
    """

    def __init__(self):
        self.router = router_model
        self.orchestrator = agent_orchestrator
        self.inference_server = local_llm_service
        logger.info("UnifiedRequestHandler initialized")

    async def handle_request(
        self,
        user_request: str,
        user_id: str,
        available_models: List[str],
        context: Optional[Dict] = None,
        stream: bool = False
    ) -> Dict:
        """
        Process user request through intelligent routing system

        Args:
            user_request: User's input text
            user_id: User ID for tracking
            available_models: List of available model names
            context: Optional context (conversation history, preferences, etc.)
            stream: Whether to stream response

        Returns:
            {
                "response": str,
                "model": str or [str],
                "path": "simple" | "complex" | "specialized",
                "routing_decision": {...},
                "confidence": float,
                "confidence_details": {...},
                "metadata": {...}
            }
        """
        start_time = datetime.now()

        logger.info(f"Handling request for user {user_id}: {user_request[:100]}...")

        # Validate input
        if not user_request or not user_request.strip():
            logger.error("Empty user_request provided")
            raise ValueError("Empty user_request")

        # STEP 1: Route the request
        routing_decision = await self.router.route(user_request, context)

        logger.info(
            f"Routing decision: path={routing_decision['path']}, "
            f"complexity={routing_decision['complexity']:.2f}, "
            f"confidence={routing_decision['confidence']:.2f}"
        )

        # STEP 2: Execute based on path
        try:
            if routing_decision["path"] == "simple":
                # Simple path: Direct LLM response
                result = await self.orchestrator.execute_simple_request(
                    user_request=user_request,
                    routing_decision=routing_decision,
                    user_id=user_id,
                    available_models=available_models
                )

            elif routing_decision["path"] == "complex":
                # Complex path: Multi-step workflow
                result = await self.orchestrator.execute_complex_request(
                    user_request=user_request,
                    routing_decision=routing_decision,
                    user_id=user_id,
                    available_models=available_models,
                    stream=stream
                )

            else:  # specialized
                # Specialized path: Use specific model
                result = await self._execute_specialized(
                    user_request=user_request,
                    routing_decision=routing_decision,
                    user_id=user_id,
                    available_models=available_models
                )

        except Exception as e:
            logger.error(f"Request execution failed: {e}")
            # Return error response
            return {
                "response": f"Error processing request: {str(e)}",
                "model": "error",
                "path": routing_decision["path"],
                "routing_decision": routing_decision,
                "confidence": 0.0,
                "confidence_details": {
                    "confidence": 0.0,
                    "recommendation": "human_review",
                    "issues": [str(e)]
                },
                "metadata": {
                    "error": str(e),
                    "execution_time_ms": 0
                }
            }

        # Calculate execution time
        end_time = datetime.now()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000

        # STEP 3: Package response with metadata
        response = {
            "response": result.get("response", ""),
            "model": result.get("model", result.get("models_used", ["unknown"])),
            "path": routing_decision["path"],
            "routing_decision": routing_decision,
            "confidence": result.get("confidence", 0.7),
            "confidence_details": result.get("confidence_details", {}),
            "metadata": {
                **result.get("metadata", {}),
                "execution_time_ms": execution_time_ms,
                "user_id": user_id
            }
        }

        logger.info(
            f"Request completed: path={routing_decision['path']}, "
            f"confidence={result.get('confidence', 0):.2f}, "
            f"time={execution_time_ms:.0f}ms"
        )

        return response

    async def _execute_specialized(
        self,
        user_request: str,
        routing_decision: Dict,
        user_id: str,
        available_models: List[str]
    ) -> Dict:
        """
        Execute specialized request (specific model/tool)

        Currently uses simple execution, but can be extended to route to
        specialized tools, MCPs, or specific model types.
        """
        # For now, treat specialized same as simple
        # In future, can add routing to specific tools based on request type

        logger.info("Executing specialized request (using simple path for now)")

        return await self.orchestrator.execute_simple_request(
            user_request=user_request,
            routing_decision=routing_decision,
            user_id=user_id,
            available_models=available_models
        )

    def get_stats(self) -> Dict:
        """Get handler statistics"""
        return {
            "router_available": self.router is not None,
            "orchestrator_available": self.orchestrator is not None,
            "inference_server_available": self.inference_server.is_available(),
            "loaded_models": self.inference_server.get_loaded_models()
        }


# Global instance
unified_handler = UnifiedRequestHandler()

# Backwards-compatible alias expected by tests and older imports
unified_request_handler = unified_handler
