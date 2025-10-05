"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
Confidence Model Service - Validates AI outputs and detects hallucinations

Uses lightweight models to score output quality and trigger retries when needed.
Works in tandem with RouterModel to ensure high-quality responses.
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Literal
from core.services.local_llm_service import local_llm_service

logger = logging.getLogger(__name__)

RecommendationType = Literal["accept", "retry", "escalate", "human_review"]


class ConfidenceModel:
    """
    Validates outputs and detects potential issues

    Scoring Criteria:
    - Factual: Is the output accurate?
    - Consistent: Is it internally consistent?
    - Complete: Does it fully answer the request?
    - Grounded: Is it based on provided context/sources?

    Recommendations:
    - accept (confidence >= 0.8): Output is high quality
    - retry (0.6 <= confidence < 0.8): Try different model/params
    - escalate (0.4 <= confidence < 0.6): Route to more capable model
    - human_review (confidence < 0.4): Flag for manual review
    """

    def __init__(self):
        self.model_name = "qwen-0.5b"  # Small, fast model for validation
        self.server = local_llm_service
        self.threshold_accept = 0.8
        self.threshold_retry = 0.6
        self.threshold_escalate = 0.4
        logger.info("ConfidenceModel initialized")

    async def score(
        self,
        output: str,
        original_request: str,
        sources: Optional[List[str]] = None,
        context: Optional[Dict] = None,
        model_used: Optional[str] = None
    ) -> Dict:
        """
        Score output confidence and quality

        Args:
            output: Generated text to validate
            original_request: Original user request
            sources: Optional source documents/data used
            context: Optional additional context
            model_used: Name of model that generated output

        Returns:
            {
                "confidence": 0.0-1.0,
                "scores": {
                    "factual": 0.0-1.0,
                    "consistent": 0.0-1.0,
                    "complete": 0.0-1.0,
                    "grounded": 0.0-1.0
                },
                "issues": [str],
                "recommendation": "accept" | "retry" | "escalate" | "human_review",
                "reasoning": str
            }
        """
        try:
            # Check if confidence checking is available
            if not self.server.is_available():
                logger.warning("Confidence model unavailable, using heuristics")
                return self._heuristic_scoring(output, original_request)

            # Construct scoring prompt
            prompt = self._create_scoring_prompt(
                output, original_request, sources, context, model_used
            )

            # Get confidence scores from model
            result = await self.server.generate(
                prompt=prompt,
                model_name=self.model_name,
                max_tokens=256,
                temperature=0.2,  # Low temp for consistent scoring
                stop=["<|user|>", "\n\n\n"]
            )

            # Parse JSON response
            scores = json.loads(result.strip())

            # Validate and normalize scores
            scores = self._validate_scores(scores)

            # Add recommendation based on confidence
            scores["recommendation"] = self._get_recommendation(scores["confidence"])

            logger.info(
                f"Confidence score: {scores['confidence']:.2f} "
                f"(recommendation: {scores['recommendation']})"
            )

            return scores

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse confidence scores: {e}")
            return self._heuristic_scoring(output, original_request)
        except Exception as e:
            logger.error(f"Confidence scoring error: {e}")
            return self._heuristic_scoring(output, original_request)

    def _create_scoring_prompt(
        self,
        output: str,
        original_request: str,
        sources: Optional[List[str]],
        context: Optional[Dict],
        model_used: Optional[str]
    ) -> str:
        """Create prompt for confidence scoring"""
        sources_text = "\n".join(sources) if sources else "None provided"
        context_text = json.dumps(context) if context else "None"

        return f"""<|system|>
You are a quality validator. Evaluate the AI-generated output for quality and accuracy.

Score each criterion (0-1 scale):

1. **Factual** (0-1): Is the output accurate and truthful?
   - Check for factual errors, misinformation
   - Verify against sources if provided
   - 1.0 = completely accurate, 0.0 = contains false information

2. **Consistent** (0-1): Is it internally consistent?
   - Check for contradictions
   - Verify logical coherence
   - 1.0 = fully consistent, 0.0 = contradictory

3. **Complete** (0-1): Does it fully answer the request?
   - Check if all parts of request addressed
   - Verify sufficient detail provided
   - 1.0 = complete answer, 0.0 = incomplete/missing parts

4. **Grounded** (0-1): Is it based on provided context/sources?
   - Check if claims are supported by sources
   - Verify no hallucinations or made-up facts
   - 1.0 = fully grounded, 0.0 = unsupported claims

Respond ONLY with valid JSON:
{{
  "factual": 0.9,
  "consistent": 0.85,
  "complete": 0.95,
  "grounded": 0.8,
  "issues": ["List any specific issues found"],
  "reasoning": "Brief explanation of scores"
}}
<|user|>
Original Request: {original_request}

Generated Output: {output}

Sources: {sources_text}

Context: {context_text}

Model Used: {model_used or "Unknown"}
<|assistant|>
"""

    def _validate_scores(self, scores: Dict) -> Dict:
        """Validate and normalize confidence scores"""
        # Ensure all required fields exist
        scores.setdefault("factual", 0.7)
        scores.setdefault("consistent", 0.7)
        scores.setdefault("complete", 0.7)
        scores.setdefault("grounded", 0.7)
        scores.setdefault("issues", [])
        scores.setdefault("reasoning", "Automated scoring")

        # Normalize individual scores to 0-1
        for key in ["factual", "consistent", "complete", "grounded"]:
            scores[key] = max(0.0, min(1.0, float(scores[key])))

        # Calculate overall confidence (weighted average)
        scores["confidence"] = (
            scores["factual"] * 0.4 +      # Most important
            scores["consistent"] * 0.3 +    # Very important
            scores["complete"] * 0.2 +      # Important
            scores["grounded"] * 0.1        # Useful but less critical
        )

        # Ensure confidence is in valid range
        scores["confidence"] = max(0.0, min(1.0, scores["confidence"]))

        return scores

    def _get_recommendation(self, confidence: float) -> RecommendationType:
        """Get recommendation based on confidence score"""
        if confidence >= self.threshold_accept:
            return "accept"
        elif confidence >= self.threshold_retry:
            return "retry"
        elif confidence >= self.threshold_escalate:
            return "escalate"
        else:
            return "human_review"

    def _heuristic_scoring(self, output: str, original_request: str) -> Dict:
        """
        Fallback heuristic scoring when model unavailable

        Simple rules:
        - Too short output = low completeness
        - Too long output without structure = potential hallucination
        - Generic output = low grounding
        """
        output_len = len(output)
        request_len = len(original_request)

        # Length-based heuristics
        if output_len < 20:
            completeness = 0.3
        elif output_len < 50:
            completeness = 0.6
        else:
            completeness = 0.8

        # Too long without structure = might be hallucinating
        if output_len > 2000 and output.count("\n") < 3:
            factual = 0.6
        else:
            factual = 0.7

        # Generic phrases reduce grounding score
        generic_phrases = ["as an ai", "i don't have", "i cannot", "i'm not sure"]
        grounded = 0.8
        for phrase in generic_phrases:
            if phrase in output.lower():
                grounded = 0.6
                break

        # Consistency is hard to judge without model
        consistent = 0.75

        confidence = (
            factual * 0.4 +
            consistent * 0.3 +
            completeness * 0.2 +
            grounded * 0.1
        )

        return {
            "confidence": confidence,
            "scores": {
                "factual": factual,
                "consistent": consistent,
                "complete": completeness,
                "grounded": grounded
            },
            "issues": ["Heuristic scoring (model unavailable)"],
            "recommendation": self._get_recommendation(confidence),
            "reasoning": "Fallback heuristic analysis"
        }

    async def validate_multi_output(
        self,
        outputs: List[Dict],
        original_request: str
    ) -> Dict:
        """
        Validate multiple outputs (e.g., from different models) and select best

        Args:
            outputs: List of {"text": str, "model": str} dicts
            original_request: Original user request

        Returns:
            {
                "best_output": str,
                "best_model": str,
                "confidence": float,
                "all_scores": [...]
            }
        """
        scores = []

        for output_dict in outputs:
            score = await self.score(
                output=output_dict["text"],
                original_request=original_request,
                model_used=output_dict.get("model")
            )
            scores.append({
                "text": output_dict["text"],
                "model": output_dict.get("model"),
                "confidence": score["confidence"],
                "scores": score["scores"]
            })

        # Sort by confidence (highest first)
        scores.sort(key=lambda x: x["confidence"], reverse=True)

        best = scores[0]

        return {
            "best_output": best["text"],
            "best_model": best["model"],
            "confidence": best["confidence"],
            "all_scores": scores
        }

    def should_retry(self, confidence_score: float) -> bool:
        """Check if output should be retried"""
        return confidence_score < self.threshold_retry

    def should_escalate(self, confidence_score: float) -> bool:
        """Check if output should be escalated to more capable model"""
        return self.threshold_escalate <= confidence_score < self.threshold_retry

    def needs_human_review(self, confidence_score: float) -> bool:
        """Check if output needs human review"""
        return confidence_score < self.threshold_escalate


# Global instance
confidence_model = ConfidenceModel()
