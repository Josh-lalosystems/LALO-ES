# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
Action Planner Service

Creates executable action plans with recursive self-critique.
This is Step 2 of the LALO workflow:
1. Generate initial plan based on interpreted intent
2. Critique the plan
3. Refine plan based on critique
4. Repeat until confidence threshold met (max 3 iterations)
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
from dataclasses import dataclass, asdict
from core.services.ai_service import ai_service
from core.services.microservices_client import rti_client
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class ActionPlan:
    """Structured action plan"""
    steps: List[Dict]  # List of action steps
    confidence: float  # Confidence in plan quality
    iterations: int  # Number of refinement iterations
    critiques: List[str]  # Critique history
    retrieved_examples: List[Dict]  # Similar successful plans from RTI
    metadata: Dict  # Additional metadata


class ActionPlanner:
    """
    Creates and refines action plans using recursive self-critique

    Process:
    1. Generate initial plan from interpreted intent
    2. Use RTI service for plan generation (has vector memory of successful plans)
    3. Self-critique the plan
    4. Refine based on critique
    5. Repeat until confidence >= threshold or max iterations reached
    """

    def __init__(self, ai_service_instance=None, max_iterations: int = 3):
        """
        Initialize action planner

        Args:
            ai_service_instance: AIService instance
            max_iterations: Maximum refinement iterations
        """
        self.ai_service_instance = ai_service_instance or ai_service
        self.max_iterations = max_iterations
        self.confidence_threshold = 0.8

    async def create_plan(
        self,
        interpreted_intent: str,
        user_id: str,
        context: Dict = None
    ) -> ActionPlan:
        """
        Create action plan with recursive refinement

        Args:
            interpreted_intent: Semantic interpretation from Step 1
            user_id: User ID for accessing API keys
            context: Optional context (user history, available tools, etc.)

        Returns:
            ActionPlan with refined steps and confidence score
        """
        logger.info(f"Creating action plan for: {interpreted_intent[:100]}...")

        plan = None
        critiques = []
        best_confidence = 0.0

        for iteration in range(self.max_iterations):
            logger.info(f"Plan iteration {iteration + 1}/{self.max_iterations}")

            # Generate or refine plan
            if iteration == 0:
                # First iteration: Generate initial plan using RTI
                plan_result = await self._generate_initial_plan(
                    interpreted_intent,
                    user_id,
                    context
                )
            else:
                # Subsequent iterations: Refine based on critique
                plan_result = await self._refine_plan(
                    interpreted_intent,
                    plan,
                    critiques[-1],
                    user_id,
                    context
                )

            plan = plan_result

            # Critique the plan
            critique = await self._critique_plan(
                interpreted_intent,
                plan,
                user_id
            )

            critiques.append(critique["critique_text"])
            confidence = critique["confidence"]

            logger.info(f"Plan confidence: {confidence:.2f}")

            # Check if we've reached acceptable quality
            if confidence >= self.confidence_threshold:
                logger.info(f"Plan meets confidence threshold after {iteration + 1} iterations")
                break

            if confidence < best_confidence:
                # Not improving, stop iterating
                logger.info("Plan quality not improving, stopping iterations")
                break

            best_confidence = confidence

        # Return final plan
        return ActionPlan(
            steps=plan.get("steps", []),
            confidence=best_confidence,
            iterations=iteration + 1,
            critiques=critiques,
            retrieved_examples=plan.get("retrieved_examples", []),
            metadata={
                "interpreted_intent": interpreted_intent,
                "user_id": user_id,
                "final_critique": critiques[-1] if critiques else ""
            }
        )

    async def _generate_initial_plan(
        self,
        intent: str,
        user_id: str,
        context: Dict = None
    ) -> Dict:
        """
        Generate initial plan using RTI service

        RTI has vector memory of successful plans and can retrieve similar examples
        """
        try:
            # Call RTI microservice for plan generation
            rti_result = await rti_client.interpret(intent)

            # RTI returns: plan, confidence, critique, retrieved_examples
            return {
                "steps": self._parse_plan_steps(rti_result.get("plan", "")),
                "rti_confidence": rti_result.get("confidence", 0.5),
                "retrieved_examples": rti_result.get("retrieved_examples", []),
                "raw_plan": rti_result.get("plan", "")
            }

        except Exception as e:
            logger.warning(f"RTI service unavailable, using fallback planner: {e}")
            # Fallback: Generate plan using AI service directly
            return await self._fallback_plan_generation(intent, user_id)

    async def _fallback_plan_generation(self, intent: str, user_id: str) -> Dict:
        """
        Fallback plan generation when RTI is unavailable
        Uses GPT-4 directly
        """
        prompt = f"""Create a detailed action plan to accomplish this goal:

{intent}

Break down the task into clear, executable steps. For each step, specify:
1. The action to take
2. The tool or method to use
3. Expected outcome

Format as JSON:
{{
    "steps": [
        {{"step": 1, "action": "...", "tool": "...", "expected_outcome": "..."}},
        {{"step": 2, "action": "...", "tool": "...", "expected_outcome": "..."}}
    ]
}}

Provide ONLY the JSON, no other text."""

        try:
            response = await self.ai_service_instance.generate(
                prompt=prompt,
                model_name="gpt-4-turbo-preview",
                user_id=user_id,
                max_tokens=1000,
                temperature=0.5
            )

            # Parse JSON
            response_clean = response.strip()
            if response_clean.startswith("```"):
                lines = response_clean.split("\n")
                response_clean = "\n".join(lines[1:-1])

            plan_json = json.loads(response_clean)

            return {
                "steps": plan_json.get("steps", []),
                "rti_confidence": 0.6,  # Lower confidence for fallback
                "retrieved_examples": [],
                "raw_plan": response
            }

        except Exception as e:
            logger.error(f"Fallback plan generation failed: {e}")
            return {
                "steps": [{"step": 1, "action": "Unable to generate plan", "tool": "none", "expected_outcome": "error"}],
                "rti_confidence": 0.0,
                "retrieved_examples": [],
                "raw_plan": f"Error: {str(e)}"
            }

    async def _refine_plan(
        self,
        intent: str,
        current_plan: Dict,
        critique: str,
        user_id: str,
        context: Dict = None
    ) -> Dict:
        """
        Refine plan based on critique
        """
        prompt = f"""Improve this action plan based on the critique provided.

Original Goal: {intent}

Current Plan:
{json.dumps(current_plan.get('steps', []), indent=2)}

Critique:
{critique}

Create an improved plan addressing the critique. Format as JSON:
{{
    "steps": [
        {{"step": 1, "action": "...", "tool": "...", "expected_outcome": "..."}},
        {{"step": 2, "action": "...", "tool": "...", "expected_outcome": "..."}}
    ]
}}

Provide ONLY the JSON, no other text."""

        try:
            response = await self.ai_service_instance.generate(
                prompt=prompt,
                model_name="gpt-4-turbo-preview",
                user_id=user_id,
                max_tokens=1000,
                temperature=0.5
            )

            # Parse JSON
            response_clean = response.strip()
            if response_clean.startswith("```"):
                lines = response_clean.split("\n")
                response_clean = "\n".join(lines[1:-1])

            refined_json = json.loads(response_clean)

            return {
                "steps": refined_json.get("steps", []),
                "rti_confidence": current_plan.get("rti_confidence", 0.5),
                "retrieved_examples": current_plan.get("retrieved_examples", []),
                "raw_plan": response
            }

        except Exception as e:
            logger.error(f"Plan refinement failed: {e}")
            return current_plan  # Return original plan if refinement fails

    async def _critique_plan(
        self,
        intent: str,
        plan: Dict,
        user_id: str
    ) -> Dict:
        """
        Critique the plan using a separate model
        Returns dict with critique_text and confidence score
        """
        prompt = f"""Critique this action plan for accomplishing the given goal.

Goal: {intent}

Plan:
{json.dumps(plan.get('steps', []), indent=2)}

Evaluate the plan and provide:
1. Confidence score (0.0-1.0) that this plan will succeed
2. Specific critique and suggestions for improvement

Format as JSON:
{{
    "confidence": <float>,
    "critique": "<detailed critique>",
    "suggestions": [
        "<suggestion 1>",
        "<suggestion 2>"
    ]
}}

Confidence guide:
- 0.9-1.0: Excellent plan, high success probability
- 0.8-0.89: Good plan, minor improvements possible
- 0.7-0.79: Acceptable plan, but needs refinement
- 0.6-0.69: Weak plan, significant issues
- 0.0-0.59: Poor plan, major problems

Provide ONLY the JSON, no other text."""

        try:
            response = await self.ai_service_instance.generate(
                prompt=prompt,
                model_name="gpt-4-turbo-preview",
                user_id=user_id,
                max_tokens=500,
                temperature=0.3
            )

            # Parse JSON
            response_clean = response.strip()
            if response_clean.startswith("```"):
                lines = response_clean.split("\n")
                response_clean = "\n".join(lines[1:-1])

            critique_json = json.loads(response_clean)

            return {
                "confidence": critique_json.get("confidence", 0.5),
                "critique_text": critique_json.get("critique", ""),
                "suggestions": critique_json.get("suggestions", [])
            }

        except Exception as e:
            logger.error(f"Plan critique failed: {e}")
            return {
                "confidence": 0.5,
                "critique_text": f"Critique failed: {str(e)}",
                "suggestions": []
            }

    def _parse_plan_steps(self, plan_text: str) -> List[Dict]:
        """
        Parse plan text from RTI into structured steps

        RTI returns plain text plan, we need to structure it
        """
        if not plan_text:
            return []

        steps = []
        lines = plan_text.split("\n")

        step_num = 1
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                steps.append({
                    "step": step_num,
                    "action": line,
                    "tool": "auto",  # Will be determined during execution
                    "expected_outcome": "As described"
                })
                step_num += 1

        return steps


# Global action planner instance
action_planner = ActionPlanner()
