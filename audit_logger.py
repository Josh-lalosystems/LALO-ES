# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Module: AuditLogger

Purpose:
 - Record immutable, structured audit entries for:
   * Chain-of-thought reasoning steps
   * ToolConnector invocations
   * Human approval decisions
   * Memory writes and vector embedding events
   * Model feedback and tuning events

Dependencies:
 - Central audit store (PostgreSQL, Elasticsearch, etc.)
 - Python logging module or structured log output
 - (Optional) OpenTelemetry for distributed trace correlation

Best Practices:
 - Standardize logs in JSON format with consistent fields
 - Include request/session identifiers and timestamps for trace correlation
 - Avoid root-logger; use module-specific loggers
 - Centralize logs to dedicated audit datastore for security and compliance
"""

import logging
import json
from datetime import datetime

# Set up module-specific logger
logger = logging.getLogger("lalo_ai.audit_logger")
logger.setLevel(logging.INFO)

# Example handler—could be file, HTTP endpoint, or stdout in container
handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class AuditLogger:
    def __init__(self, audit_store=None):
        """
        audit_store: abstraction to write persistent audit entries.
                     Could wrap a database or log ingestion API.
        """
        self.audit_store = audit_store

    def record(self, agent_id: str, trace: list, tool_calls: list):
        """
        Logs the reasoning trace and tool call metadata for the agent execution.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "trace": trace,
            "tool_calls": tool_calls,
            "event": "agent_execution"
        }
        self._commit(entry)

    def record_error(self, agent_id: str, error_code: str, error_message: str):
        """
        Logs errors encountered during reasoning or execution.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "error_code": error_code,
            "error_message": error_message,
            "event": "execution_error"
        }
        self._commit(entry)

    def record_memory(self, agent_id: str, redis_key: str, vector_id: str):
        """
        Logs memory write linkage between Redis and vector stores.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "redis_key": redis_key,
            "vector_id": vector_id,
            "event": "memory_write"
        }
        self._commit(entry)

    def record_approval(self, agent_id: str, approval_id: str, actor: str, status: str):
        """
        Logs human approval decisions associated with specific plan IDs.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "approval_id": approval_id,
            "approved_by": actor,
            "status": status,
            "event": "approval_decision"
        }
        self._commit(entry)

    def _commit(self, entry: dict):
        """
        Internal commit: serialize and either send to audit_store or log.
        """
        serialized = json.dumps(entry)
        if self.audit_store:
            try:
                self.audit_store.write(entry)
            except Exception as e:
                logger.error(f"Audit store write failed: {e}")
                logger.info(serialized)
        else:
            # fallback to stdout or container log
            logger.info(serialized)
