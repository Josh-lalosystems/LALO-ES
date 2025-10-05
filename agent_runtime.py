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
Module: AgentRuntime

Purpose:
 - Decides whether to use HRM (Hierarchical Reasoning Model) or Chain-of-Thought LLM
 - Executes agent plan steps via ToolConnectors
 - Streams chain-of-thought trace to UI and logs audit/tracing data
 - Routes through HumanApproval gate when modifying production systems
 - Flags hallucinations and handles tool failures robustly

Dependencies:
 - hrm_adapter.HrmAdapter
 - LLM client (OpenAI/GPT/etc.)
 - ToolConnector (api or ui)
 - AuditLogger
 - HumanApprovalGate
 - MemoryManager
 - FeedbackLoop

Edge Cases Handled:
 - HRM plan unsupported or error → fallback to LLM
 - LLM timeout or exception
 - Tool connector failure per step
 - Human approval denied or timed out
 - Hallucination detection via missing / inconsistent output
"""

from .hrm_adapter import HrmAdapter
from .tool_connector_api import ApiToolConnector
from .tool_connector_ui import UiToolConnector
from .audit_logger import AuditLogger
from .human_approval import HumanApprovalGate
from .memory_manager import MemoryManager
from .feedback_loop import FeedbackLoop

class AgentRuntimeError(Exception):
    pass

class AgentRuntime:
    def __init__(self, agent, use_hrm: bool = True):
        self.agent = agent
        self.trace = []           # chain-of-thought or HRM plan
        self.tool_calls = []      # tool usage log
        self.audit = AuditLogger()
        self.memory = MemoryManager()
        self.approval = HumanApprovalGate()
        self.feedback = FeedbackLoop()
        self.hrm = HrmAdapter()
        self.use_hrm = use_hrm

    def run(self):
        """ Main execution entry point for agent. """
        mode = "HRM" if self.use_hrm and self.hrm.supports(self.agent.request) else "LLM"
        try:
            if mode == "HRM":
                plan, steps = self.hrm.plan_and_execute(self.agent.request)
                self.trace = plan.steps
            else:
                plan = self.agent.llm.generate_chain_of_thought(self.agent.request)
                self.trace = plan.steps
                steps = plan.steps
        except Exception as e:
            self.audit.record_error(self.agent.id, "REASONER_FAILURE", str(e))
            raise AgentRuntimeError(f"{mode} execution failed: {e}")

        for step in steps:
            self.trace.append(step)

            if step.modifies_production:
                approval_id = self.approval.request_approval(self.agent.id, plan.summary())
                self.approval.poll_approval(approval_id)

            connector = ApiToolConnector() if step.use_api else UiToolConnector()
            try:
                result = connector.execute(step.tool_name, step.input_data)
                summary = result.summary
            except Exception as te:
                self.tool_calls.append({"step_id": step.id, "tool": step.tool_name, "error": str(te)})
                self.audit.record(self.agent.id, self.trace, self.tool_calls)
                raise AgentRuntimeError(f"Tool execution failed at step {step.id}: {te}")

            call_record = {"step_id": step.id, "tool": step.tool_name, "result_summary": summary}
            if summary is None or result.hallucinatory:
                call_record["hallucination_flag"] = True

            self.tool_calls.append(call_record)

        # Log trace and result
        self.audit.record(self.agent.id, self.trace, self.tool_calls)

        # Store session memory
        self.memory.store_session(self.agent.id, self.agent.request, self.trace, self.tool_calls)

        # Feedback loop entry
        self.feedback.collect_feedback(self.agent.id, self.trace, self.tool_calls)

        return {
            "agent_id": self.agent.id,
            "trace": self.trace,
            "last_result": self.tool_calls[-1]["result_summary"]
        }
