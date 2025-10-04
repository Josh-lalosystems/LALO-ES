# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
Semantic Interpretation Service

Wraps the ConfidenceSystem to provide semantic interpretation with confidence scoring.
This is Step 1 of the LALO workflow:
1. User request → Semantic interpretation
2. Confidence scoring
3. Clarification if needed
"""

from confidence_system import ConfidenceSystem, InterpretationResult
from core.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)


class SemanticInterpreter:
    """
    Semantic interpretation service for LALO workflow Step 1

    Uses the existing ConfidenceSystem which provides:
    - Fast semantic interpretation (GPT-3.5)
    - Confidence scoring (GPT-4)
    - Clarification suggestions
    - Feedback requirement detection
    """

    def __init__(self, ai_service_instance=None):
        """
        Initialize semantic interpreter

        Args:
            ai_service_instance: AIService instance (defaults to global ai_service)
        """
        self.ai_service_instance = ai_service_instance or ai_service
        self._confidence_systems = {}  # Cache per user

    def _get_confidence_system(self, user_id: str) -> ConfidenceSystem:
        """
        Get or create ConfidenceSystem for user

        Args:
            user_id: User ID

        Returns:
            ConfidenceSystem instance
        """
        if user_id not in self._confidence_systems:
            self._confidence_systems[user_id] = ConfidenceSystem(
                ai_service=self.ai_service_instance,
                user_id=user_id,
                interpreter_model="gpt-3.5-turbo",  # Fast interpretation
                confidence_model="gpt-4-turbo-preview",  # Robust confidence
                min_confidence_threshold=0.75  # Threshold for requiring clarification
            )
        return self._confidence_systems[user_id]

    async def interpret(
        self,
        user_request: str,
        user_id: str,
        context: dict = None
    ) -> InterpretationResult:
        """
        Interpret user request with confidence scoring

        This is the entry point for LALO workflow Step 1:
        - Extracts semantic intent from user request
        - Scores confidence in interpretation
        - Generates clarification questions if needed
        - Returns structured result

        Args:
            user_request: The user's original request
            user_id: User ID for accessing API keys
            context: Optional context (conversation history, etc.)

        Returns:
            InterpretationResult with:
            - interpreted_intent: What the user wants to accomplish
            - confidence_score: 0.0-1.0 confidence in interpretation
            - reasoning_trace: Step-by-step reasoning
            - suggested_clarifications: Questions to ask if confidence is low
            - feedback_required: Whether human clarification is needed
        """
        try:
            logger.info(f"Interpreting request for user {user_id}: {user_request[:100]}...")

            # Get confidence system for this user
            confidence_system = self._get_confidence_system(user_id)

            # Run interpretation
            result = await confidence_system.interpret_request(user_request)

            logger.info(
                f"Interpretation complete. Confidence: {result.confidence_score:.2f}, "
                f"Feedback required: {result.feedback_required}"
            )

            return result

        except Exception as e:
            logger.error(f"Error in semantic interpretation: {e}")
            # Return error result
            return InterpretationResult(
                original_request=user_request,
                interpreted_intent=f"Error during interpretation: {str(e)}",
                confidence_score=0.0,
                reasoning_trace=[f"Interpretation failed: {str(e)}"],
                suggested_clarifications=[
                    "Could you please rephrase your request?",
                    "Please provide more details about what you'd like to accomplish"
                ],
                model_metadata={"error": str(e)},
                feedback_required=True
            )

    async def refine_with_feedback(
        self,
        original_request: str,
        user_feedback: str,
        user_id: str,
        previous_result: InterpretationResult = None
    ) -> InterpretationResult:
        """
        Refine interpretation with user feedback

        When initial interpretation has low confidence, user provides feedback.
        This method combines original request + feedback for better interpretation.

        Args:
            original_request: Original user request
            user_feedback: User's clarification/feedback
            user_id: User ID
            previous_result: Previous interpretation result

        Returns:
            New InterpretationResult with refined understanding
        """
        # Combine original request with feedback
        combined_request = f"{original_request}\n\nUser clarification: {user_feedback}"

        logger.info(f"Refining interpretation with user feedback for user {user_id}")

        # Re-run interpretation with combined context
        return await self.interpret(combined_request, user_id)


# Global interpreter instance
semantic_interpreter = SemanticInterpreter()
