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
- Robust: Confidence scoring (e.g., Claude-2 for detailed analysis)
- Planning: HRM from Sapient AI for complex planning
- Specialized: Liquid Nanos for specific tasks
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
import anthropic
from .hrm_adapter import HrmAdapter
from .audit_logger import AuditLogger

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
    model_metadata: Dict[str, any]
    feedback_required: bool = False

class ConfidenceSystem:
    def __init__(self, 
                 interpreter_model: str = "gpt-3.5-turbo",
                 confidence_model: str = "claude-2",
                 min_confidence_threshold: float = 0.85):
        self.interpreter_model = interpreter_model
        self.confidence_model = confidence_model
        self.min_confidence_threshold = min_confidence_threshold
        self.hrm_adapter = HrmAdapter()
        self.audit = AuditLogger()
        
    async def interpret_request(self, user_request: str) -> InterpretationResult:
        """
        First stage: Quick semantic interpretation using lightweight model
        """
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
        
        # Log the interpretation attempt
        self.audit.log_interpretation(result)
        
        return result

    async def _run_interpreter_model(self, user_request: str) -> str:
        """
        Runs the lightweight model for quick semantic interpretation
        """
        if "gpt" in self.interpreter_model:
            response = await openai.ChatCompletion.create(
                model=self.interpreter_model,
                messages=[
                    {"role": "system", "content": "You are a semantic interpreter. Extract the core intent from user requests accurately and concisely."},
                    {"role": "user", "content": user_request}
                ],
                temperature=0.3  # Lower temperature for more consistent interpretations
            )
            return response.choices[0].message.content
        # Add support for other model types as needed
    
    async def _analyze_confidence(self, original: str, interpretation: str) -> Dict:
        """
        Uses the robust model to analyze confidence in the interpretation
        """
        if self.confidence_model == "claude-2":
            prompt = f"""
            Analyze the following interpretation of a user request:

            Original Request: {original}
            System Interpretation: {interpretation}

            Provide:
            1. Confidence score (0.0-1.0)
            2. Reasoning trace
            3. Suggested clarifications if needed

            Format response as JSON with keys: score, reasoning, clarifications
            """
            
            response = await anthropic.messages.create(
                model=self.confidence_model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return json.loads(response.content)
        # Add support for other model types as needed

    def requires_clarification(self, result: InterpretationResult) -> bool:
        """
        Determines if the confidence score requires user clarification
        """
        return (
            result.confidence_score < self.min_confidence_threshold or
            len(result.suggested_clarifications) > 0
        )

    def collect_feedback(self, result: InterpretationResult, user_feedback: str) -> None:
        """
        Collects and stores user feedback for future improvements
        """
        feedback_data = {
            "original_request": result.original_request,
            "interpretation": result.interpreted_intent,
            "confidence_score": result.confidence_score,
            "user_feedback": user_feedback,
            "model_metadata": result.model_metadata
        }
        self.audit.log_feedback(feedback_data)
