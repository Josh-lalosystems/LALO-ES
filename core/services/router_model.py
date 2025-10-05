"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
Router Model Service - Intelligent request classification and routing

First-touch layer that determines the optimal execution path for each request.
Uses lightweight models for fast classification (<1s response time).
"""

import json
import logging
import asyncio
from typing import Dict, Literal, Optional
from core.services.local_llm_service import local_llm_service

logger = logging.getLogger(__name__)

PathType = Literal["simple", "complex", "specialized"]


class RouterModel:
    """
    First-touch router that classifies requests and determines execution path

    Routing Decision Matrix:
    - Complexity 0-0.3, Confidence >0.8 → Simple path (direct LLM)
    - Complexity 0.3-0.6 → Specialized model
    - Complexity >0.6 → Complex path (Agent Orchestrator)
    """

    def __init__(self):
        self.model_name = "liquid-tool"  # Fast 1.2B model for routing
        self.server = local_llm_service
        self.fallback_enabled = True
        logger.info("RouterModel initialized")

    async def route(self, user_request: str, context: Optional[Dict] = None) -> Dict:
        """
        Analyze request and determine optimal execution path

        Args:
            user_request: User's input text
            context: Optional context (conversation history, user preferences, etc.)

        Returns:
            {
                "path": "simple" | "complex" | "specialized",
                "complexity": 0.0-1.0,
                "confidence": 0.0-1.0,
                "reasoning": str,
                "recommended_model": str,
                "requires_tools": bool,
                "requires_workflow": bool
            }
        """
        try:
            # Quick deterministic short-circuit for trivial/syntactic math or short factual questions
            try:
                low_request = (user_request or "").lower()
                # Simple math detection (e.g., 'what is 2 + 2')
                if any(op in low_request for op in ['+', '-', '*', '/']) and len(low_request) < 80:
                    return {
                        "complexity": 0.1,
                        "confidence": 0.95,
                        "path": "simple",
                        "reasoning": "Deterministic math detection",
                        "recommended_model": "tinyllama",
                        "requires_tools": False,
                        "requires_workflow": False
                    }
            except Exception:
                pass

            # Check if local inference is available
            if not self.server.is_available():
                logger.warning("Local inference not available, using fallback routing")
                return await self._fallback_routing(user_request)

            # Construct routing prompt
            prompt = self._create_routing_prompt(user_request, context)

            # Get routing decision from model
            result = await self.server.generate(
                prompt=prompt,
                model_name=self.model_name,
                max_tokens=256,
                temperature=0.3,  # Low temp for consistent routing
                stop=["<|user|>", "\n\n\n"]
            )

            # Parse JSON response
            decision = json.loads(result.strip())

            # Validate and normalize decision
            decision = self._validate_decision(decision)

            logger.info(
                f"Routing: {decision['path']} "
                f"(complexity={decision['complexity']:.2f}, "
                f"confidence={decision['confidence']:.2f})"
            )

            return decision

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse routing decision: {e}")
            logger.warning(f"Raw response: {result}")
            return await self._fallback_routing(user_request)
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return await self._fallback_routing(user_request)

    def _create_routing_prompt(self, user_request: str, context: Optional[Dict]) -> str:
        """Create routing prompt for the model"""
        return f"""<|system|>
You are a request router. Analyze the user request and determine the optimal execution path.

Classify the request based on:

1. **Complexity** (0-1 scale):
   - 0.0-0.3: Simple factual question, direct answer
   - 0.3-0.6: Moderate complexity, may need specialized model
   - 0.6-1.0: Complex, multi-step reasoning or workflow needed

2. **Confidence** (0-1 scale):
   - <0.7: Need specialized model or validation
   - 0.7-0.9: Can handle with standard LLM
   - >0.9: Simple, direct answer

3. **Path Selection**:
   - "simple": Direct LLM response (for basic questions)
   - "complex": Multi-step workflow (for research, analysis, creation)
   - "specialized": Specific model/tool (for extraction, math, code)

4. **Resource Requirements**:
   - requires_tools: Does it need web search, file access, etc?
   - requires_workflow: Does it need multi-step orchestration?

Respond ONLY with valid JSON in this exact format:
{{
  "complexity": 0.5,
  "confidence": 0.8,
  "path": "simple",
  "reasoning": "Brief explanation of classification",
  "recommended_model": "tinyllama",
  "requires_tools": false,
  "requires_workflow": false
}}
<|user|>
Request: {user_request}
Context: {json.dumps(context) if context else "None"}
<|assistant|>
"""

    def _validate_decision(self, decision: Dict) -> Dict:
        """Validate and normalize routing decision"""
        # Ensure required fields exist
        decision.setdefault("complexity", 0.5)
        decision.setdefault("confidence", 0.7)
        decision.setdefault("path", "simple")
        decision.setdefault("reasoning", "Auto-classified")
        decision.setdefault("recommended_model", "tinyllama")
        decision.setdefault("requires_tools", False)
        decision.setdefault("requires_workflow", False)

        # Normalize values
        decision["complexity"] = max(0.0, min(1.0, float(decision["complexity"])))
        decision["confidence"] = max(0.0, min(1.0, float(decision["confidence"])))

        # Validate path
        if decision["path"] not in ["simple", "complex", "specialized"]:
            decision["path"] = "simple"

        # Auto-adjust path based on complexity
        if decision["complexity"] > 0.7:
            decision["path"] = "complex"
        elif decision["complexity"] < 0.3 and decision["confidence"] > 0.8:
            decision["path"] = "simple"

        return decision

    async def _fallback_routing(self, request: str) -> Dict:
        """Fallback routing using simple heuristics when model unavailable"""
        complexity = self.estimate_complexity_sync(request)

        # Determine path based on complexity
        if complexity < 0.3:
            path = "simple"
            model = "tinyllama"
        elif complexity > 0.6:
            path = "complex"
            model = "tinyllama"
        else:
            path = "specialized"
            model = "liquid-tool"

        return {
            "complexity": complexity,
            "confidence": 0.6,
            "path": path,
            "reasoning": "Heuristic-based routing (model unavailable)",
            "recommended_model": model,
            "requires_tools": self._check_tool_keywords(request),
            "requires_workflow": complexity > 0.6
        }

    def estimate_complexity_sync(self, request: str) -> float:
        """
        Quick complexity estimation using heuristics

        Returns complexity score 0-1
        """
        request_lower = request.lower()

        # Complexity indicators
        simple_keywords = [
            'what is', 'define', 'who is', 'when did', 'where is',
            'how many', 'what does', 'meaning of'
        ]

        medium_keywords = [
            'how to', 'compare', 'explain', 'summarize', 'list',
            'describe', 'why', 'difference between'
        ]

        complex_keywords = [
            'design', 'analyze', 'research', 'create plan', 'optimize',
            'develop', 'implement', 'architecture', 'strategy',
            'investigate', 'solve', 'calculate complex'
        ]

        # Check keywords
        if any(kw in request_lower for kw in complex_keywords):
            base_score = 0.8
        elif any(kw in request_lower for kw in medium_keywords):
            base_score = 0.5
        elif any(kw in request_lower for kw in simple_keywords):
            base_score = 0.2
        else:
            base_score = 0.4  # Default medium

        # Adjust based on length (longer = more complex)
        word_count = len(request.split())
        length_factor = min(word_count / 100, 0.3)  # Cap at 0.3

        # Adjust based on questions (multiple questions = more complex)
        question_count = request.count('?')
        question_factor = min(question_count * 0.1, 0.2)

        final_score = min(base_score + length_factor + question_factor, 1.0)

        return final_score

    def _check_tool_keywords(self, request: str) -> bool:
        """Check if request likely needs tools"""
        request_lower = request.lower()

        tool_keywords = [
            'search', 'find information', 'look up', 'browse',
            'read file', 'open file', 'save', 'write to',
            'execute', 'run', 'calculate', 'compute',
            'latest', 'current', 'today', 'news'
        ]

        return any(kw in request_lower for kw in tool_keywords)

    async def estimate_complexity_async(self, request: str) -> float:
        """
        Async version of complexity estimation (for future model-based estimation)

        Currently wraps sync version, but can be extended to use ML models
        """
        return self.estimate_complexity_sync(request)


# Global instance
router_model = RouterModel()
