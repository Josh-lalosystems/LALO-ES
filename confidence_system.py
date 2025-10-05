# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Module: ConfidenceSystem

Purpose:
- Implements a multi-model confidence scoring system
- Handles semantic interpretation of user requests
- Manages feedback loops for request clarification
- Integrates with multiple LLM providers for different aspects
- Provides detailed confidence metrics and explanations

Models Used:
- Lightweight: Fast semantic interpretation (e.g., GPT-3.5-turbo for quick understanding)
- Robust: Confidence scoring (e.g., Claude Haiku for detailed analysis)
- Planning: Claude Sonnet for complex planning
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

class ModelType(Enum):
    INTERPRETER = "interpreter"
    CONFIDENCE = "confidence"
    PLANNER = "planner"
    SPECIALIZED = "specialized"

@dataclass
class InterpretationResult:
    original_request: str
    interpreted_intent: str
    confidence_score: float
    reasoning_trace: List[str]
    suggested_clarifications: List[str]
    model_metadata: Dict
    feedback_required: bool = False
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

class ConfidenceSystem:
    def __init__(self,
                 ai_service,
                 user_id: str,
                 interpreter_model: str = "gpt-3.5-turbo",
                 confidence_model: str = "gpt-4-turbo-preview",  # Changed from Claude to GPT
                 min_confidence_threshold: float = 0.85):
        """
        Initialize confidence system with AI service integration

        Args:
            ai_service: The AI service instance with initialized models
            user_id: User ID for accessing their API keys
            interpreter_model: Fast model for semantic interpretation
            confidence_model: Robust model for confidence analysis (now GPT instead of Claude)
            min_confidence_threshold: Minimum acceptable confidence score
        """
        self.ai_service = ai_service
        self.user_id = user_id
        self.interpreter_model = interpreter_model
        self.confidence_model = confidence_model
        self.min_confidence_threshold = min_confidence_threshold
        
    async def interpret_request(self, user_request: str) -> InterpretationResult:
        """
        First stage: Quick semantic interpretation using lightweight model

        Returns:
            InterpretationResult with interpretation, confidence, and suggestions
        """
        try:
            # Initial interpretation using fast model
            interpretation = await self._run_interpreter_model(user_request)

            # Get confidence score using robust model
            confidence_analysis = await self._analyze_confidence(
                user_request,
                interpretation
            )

            result = InterpretationResult(
                original_request=user_request,
                interpreted_intent=interpretation,
                confidence_score=confidence_analysis["score"],
                reasoning_trace=confidence_analysis["reasoning"],
                suggested_clarifications=confidence_analysis["clarifications"],
                model_metadata={
                    "interpreter": self.interpreter_model,
                    "confidence": self.confidence_model
                }
            )

            # Determine if feedback is required
            result.feedback_required = self.requires_clarification(result)

            return result

        except Exception as e:
            # Return error result
            return InterpretationResult(
                original_request=user_request,
                interpreted_intent=f"Error: {str(e)}",
                confidence_score=0.0,
                reasoning_trace=[f"Interpretation failed: {str(e)}"],
                suggested_clarifications=["Please rephrase your request"],
                model_metadata={"error": str(e)},
                feedback_required=True
            )

    async def _run_interpreter_model(self, user_request: str) -> str:
        """
        Runs the lightweight model for quick semantic interpretation
        Uses the existing ai_service with user's API keys
        """
        prompt = f"""You are LALO, a semantic interpreter. Your job is to extract the core intent from user requests.

User Request: {user_request}

Analyze this request and provide:
1. What the user wants to accomplish
2. Any specific actions or steps implied
3. Key entities or systems mentioned

Be accurate and concise. Format as a clear interpretation statement."""

        # Use ai_service to generate interpretation
        interpretation = await self.ai_service.generate(
            prompt=prompt,
            model_name=self.interpreter_model,
            user_id=self.user_id,
            max_tokens=300,
            temperature=0.3  # Lower temperature for consistency
        )

        return interpretation

    async def _analyze_confidence(self, original: str, interpretation: str) -> Dict:
        """
        Uses the robust model to analyze confidence in the interpretation
        Returns dict with score, reasoning, and clarifications
        """
        prompt = f"""Analyze this interpretation of a user request and provide a confidence assessment.

Original Request: "{original}"

System Interpretation: "{interpretation}"

Provide your analysis in the following JSON format:
{{
    "score": <float between 0.0 and 1.0>,
    "reasoning": [
        "<reasoning step 1>",
        "<reasoning step 2>",
        "<reasoning step 3>"
    ],
    "clarifications": [
        "<clarification question 1 if needed>",
        "<clarification question 2 if needed>"
    ]
}}

Confidence scoring guide:
- 0.95-1.0: Perfect clarity, no ambiguity
- 0.85-0.94: Very clear, minor assumptions
- 0.70-0.84: Clear but could use confirmation
- 0.50-0.69: Somewhat ambiguous, needs clarification
- 0.0-0.49: Very unclear, needs significant clarification

Provide ONLY the JSON, no other text."""

        # Use ai_service with confidence model
        response = await self.ai_service.generate(
            prompt=prompt,
            model_name=self.confidence_model,
            user_id=self.user_id,
            max_tokens=500,
            temperature=0.2
        )

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_clean = response.strip()
            if response_clean.startswith("```"):
                # Remove markdown code block markers
                lines = response_clean.split("\n")
                response_clean = "\n".join(lines[1:-1])

            analysis = json.loads(response_clean)

            # Validate structure
            if "score" not in analysis:
                analysis["score"] = 0.5
            if "reasoning" not in analysis:
                analysis["reasoning"] = ["Confidence analysis completed"]
            if "clarifications" not in analysis:
                analysis["clarifications"] = []

            return analysis

        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            import logging
            logger = logging.getLogger('confidence_system')
            logger.warning("Failed to parse confidence analysis JSON: %s", e)
            logger.debug("Response was: %s", response)
            return {
                "score": 0.7,
                "reasoning": ["Automated confidence assessment"],
                "clarifications": []
            }

    def requires_clarification(self, result: InterpretationResult) -> bool:
        """
        Determines if the confidence score requires user clarification
        """
        return (
            result.confidence_score < self.min_confidence_threshold or
            len(result.suggested_clarifications) > 0
        )
