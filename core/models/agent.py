# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Agent Model

Defines custom AI agents with configurations, tools, and guardrails
"""

from sqlalchemy import Column, String, JSON, Boolean, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from core.database import Base


class Agent(Base):
    """
    Custom AI Agent Definition
    """
    __tablename__ = "agents"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Basic Info
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, default="general")  # general, coding, research, creative, etc.

    # AI Configuration
    system_prompt = Column(String, nullable=False)
    model = Column(String, default="gpt-3.5-turbo")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)
    top_p = Column(Float, default=1.0)
    frequency_penalty = Column(Float, default=0.0)
    presence_penalty = Column(Float, default=0.0)

    # Tools & Permissions
    allowed_tools = Column(JSON, default=list)  # List of tool names agent can use
    required_permissions = Column(JSON, default=list)  # Permissions needed to use this agent

    # Guardrails
    guardrails = Column(JSON, default=list)  # List of guardrail rules
    max_iterations = Column(Integer, default=10)  # Max workflow iterations
    timeout_seconds = Column(Integer, default=300)  # Execution timeout

    # Sharing & Visibility
    is_public = Column(Boolean, default=False)  # Visible in marketplace
    is_template = Column(Boolean, default=False)  # Can be cloned
    parent_agent_id = Column(String, nullable=True)  # If cloned from another agent

    # Versioning
    version = Column(Integer, default=1)
    version_notes = Column(String, nullable=True)

    # Metadata
    tags = Column(JSON, default=list)  # Search tags
    icon = Column(String, nullable=True)  # Icon/emoji for UI
    color = Column(String, default="#3B82F6")  # UI color

    # Stats
    usage_count = Column(Integer, default=0)
    rating_average = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime, nullable=True)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "system_prompt": self.system_prompt,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "allowed_tools": self.allowed_tools,
            "required_permissions": self.required_permissions,
            "guardrails": self.guardrails,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "is_public": self.is_public,
            "is_template": self.is_template,
            "parent_agent_id": self.parent_agent_id,
            "version": self.version,
            "version_notes": self.version_notes,
            "tags": self.tags,
            "icon": self.icon,
            "color": self.color,
            "usage_count": self.usage_count,
            "rating_average": self.rating_average,
            "rating_count": self.rating_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None
        }


class AgentRating(Base):
    """
    User ratings for agents
    """
    __tablename__ = "agent_ratings"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    rating = Column(Float, nullable=False)  # 1-5 stars
    review = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AgentExecution(Base):
    """
    Track agent executions for analytics
    """
    __tablename__ = "agent_executions"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    workflow_session_id = Column(String, ForeignKey("workflow_sessions.session_id"), nullable=True)

    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="running")  # running, completed, failed, timeout
    error_message = Column(String, nullable=True)

    tools_used = Column(JSON, default=list)  # Tools executed during run
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    execution_time_ms = Column(Integer, nullable=True)
