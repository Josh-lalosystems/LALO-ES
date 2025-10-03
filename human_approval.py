# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Module: HumanApprovalGate

Purpose:
 - Enforces human-in-the-loop oversight before any agent action modifies production systems.
 - Supports standard approval workflows for AI-generated plans (interactive or automated routing).
 - Logs approval decisions via AuditLogger.

Dependencies:
 - AuditLogger to record structured decisions
 - External notifier (e.g. email, Slack, dashboard)
 - Approval store/state tracking (e.g. database record of pending approvals)

Edge Cases:
 - Timeout if approval not received within allowed window
 - Denial handling (raises exception, halts runtime)
 - Auto-approve low-risk actions if policy allows
 - Multi-approver or escalation paths
"""

import uuid
import time
from .audit_logger import AuditLogger

class ApprovalError(Exception):
    pass

class HumanApprovalGate:
    def __init__(self, timeout_seconds: int = 3600, auto_approve_low_risk: bool = False):
        self.audit = AuditLogger()
        self.timeout = timeout_seconds
        self.auto_ok = auto_approve_low_risk
        self.pending = {}  # approval_id → metadata store

    def request_approval(self, agent_id: str, plan_summary: str) -> str:
        """
        Initiates an approval request, returns approval_id.
        """
        approval_id = str(uuid.uuid4())
        self.pending[approval_id] = {
            "agent_id": agent_id,
            "plan": plan_summary,
            "status": "pending",
            "requested_at": time.time()
        }
        # TODO: Send notification via configured channel (Slack, email, UI)
        self.audit.record(entry={
            "approval_id": approval_id,
            "agent_id": agent_id,
            "plan_summary": plan_summary,
            "status": "requested",
            "event": "approval_requested"
        })
        return approval_id

    def poll_approval(self, approval_id: str):
        """
        Blocks until approval is granted or timeout.
        """
        entry = self.pending.get(approval_id)
        if not entry:
            raise ApprovalError("Invalid approval_id")

        if self.auto_ok and entry.get("plan", "").lower().find("low risk") != -1:
            entry["status"] = "approved"
            self.audit.record(self._make_log(approval_id, entry, "auto_approved"))
            return True

        start = entry["requested_at"]
        while True:
            # Poll status (should be updated externally via approve/deny endpoint)
            status = entry.get("status")
            if status == "approved":
                self.audit.record(self._make_log(approval_id, entry, "approved"))
                return True
            if status == "denied":
                self.audit.record(self._make_log(approval_id, entry, "denied"))
                raise ApprovalError("Human denied the plan execution")
            if time.time() - start > self.timeout:
                self.audit.record(self._make_log(approval_id, entry, "timeout"))
                raise ApprovalError("Approval timeout")
            time.sleep(5)

    def set_status(self, approval_id: str, actor: str, status: str):
        """
        External interface to update approval (e.g., from UI or API endpoint).
        """
        if approval_id not in self.pending:
            raise ApprovalError("Invalid approval_id")
        self.pending[approval_id]["status"] = status
        self.pending[approval_id]["actor"] = actor
        self.audit.record(self._make_log(approval_id, self.pending[approval_id], status))

    def _make_log(self, approval_id, entry, status):
        return {
            "approval_id": approval_id,
            "agent_id": entry["agent_id"],
            "status": status,
            "actor": entry.get("actor"),
            "plan_summary": entry.get("plan"),
            "event": "approval_decision"
        }
