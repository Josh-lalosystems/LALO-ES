"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Module: HrmAdapter

Purpose:
 - Provides optional high-speed reasoning via a Hierarchical Reasoning Model (HRM)
   based on Sapient Intelligence’s recent HRM architecture (brain-inspired, two-module,
   planning + execution, ~27M parameters, trained with only ~1,000 examples).:contentReference[oaicite:1]{index=1}
 - Offers parallel, latent reasoning path as a low-latency alternative to large LLM chain-of-thought
 - Routes to fallback chain-of-thought if HRM is unsupported or confidence is low

Dependencies:
 - HRM model weights (local or remote-serving)
 - Embedding or classifier to evaluate HRM confidence
 - Graceful fallback mechanism to LLM
 - AuditLogger for logging HRM decisions

Edge Cases & Handling:
 - HRM unsupported: fallback to LLM planning
 - HRM confidence low: fallback to Chain-of-Thought
 - HRM runtime error: catch and abort to LLM
"""

from .audit_logger import AuditLogger

class HrmAdapter:
    def __init__(self, hrm_model=None, confidence_threshold=0.8):
        self.hrm_model = hrm_model  # replace with actual HRM instance or loader
        self.conf_thresh = confidence_threshold
        self.audit = AuditLogger()

    def supports(self, user_request: dict) -> bool:
        """
        Quick check whether HRM is applicable for this request.
        For example: deterministic, puzzle-like, structured workloads.
        """
        return self.hrm_model is not None and user_request.get("structured_task", False)

    def plan_and_execute(self, user_request: dict):
        """
        Executes planning via HRM:
         - High-level abstract plan
         - Low-level rapid execution steps
         - Single forward pass with latent reasoning
        Fallback occurs if confidence is below threshold.
        """
        try:
            plan, steps, confidence = self.hrm_model.run(user_request)
        except Exception as e:
            self.audit.record_error(user_request.get("agent_id", "unknown"),
                                     "HRM_RUNTIME_ERROR", str(e))
            raise

        if confidence < self.conf_thresh:
            self.audit.record(user_request.get("agent_id", "unknown"),
                               trace=[{"warning": "HRM confidence low, fallback to LLM"}],
                               tool_calls=[])
            raise RuntimeError("HRM confidence below threshold")

        # Log that HRM path was used
        self.audit.record(user_request.get("agent_id", "unknown"),
                          trace=[{"event": "HRM_plan", "confidence": confidence}],
                          tool_calls=[])

        return plan, steps
