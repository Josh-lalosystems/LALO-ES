# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Agent Manager Service

Manages custom AI agent definitions, validation, and lifecycle
"""

from typing import List, Optional, Dict
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import or_
from core.models.agent import Agent, AgentRating, AgentExecution
from core.database import SessionLocal
from core.validators import validate_agent_config


class AgentManager:
    """Service for managing AI agents"""

    def __init__(self):
        self.agent_templates = self._load_default_templates()

    def _load_default_templates(self) -> List[Dict]:
        """Load default agent templates"""
        return [
            {
                "name": "Code Assistant",
                "description": "Helps with coding tasks, debugging, and code review",
                "category": "coding",
                "system_prompt": "You are an expert software engineer. Help users with coding tasks, debugging, code review, and best practices.",
                "model": "gpt-4-turbo-preview",
                "allowed_tools": ["code_executor", "web_search", "file_operations"],
                "icon": "💻",
                "color": "#10B981"
            },
            {
                "name": "Research Assistant",
                "description": "Conducts research and provides comprehensive analysis",
                "category": "research",
                "system_prompt": "You are a research assistant. Help users find information, analyze data, and provide comprehensive research reports.",
                "model": "gpt-4-turbo-preview",
                "allowed_tools": ["web_search", "rag_query", "file_operations"],
                "icon": "🔬",
                "color": "#3B82F6"
            },
            {
                "name": "Creative Writer",
                "description": "Creates creative content, stories, and marketing copy",
                "category": "creative",
                "system_prompt": "You are a creative writer. Help users create engaging content, stories, and marketing materials.",
                "model": "claude-3-5-sonnet-20241022",
                "allowed_tools": ["web_search", "image_generator"],
                "icon": "✍️",
                "color": "#8B5CF6"
            },
            {
                "name": "Data Analyst",
                "description": "Analyzes data and generates insights",
                "category": "analysis",
                "system_prompt": "You are a data analyst. Help users analyze data, create visualizations, and generate insights.",
                "model": "gpt-4-turbo-preview",
                "allowed_tools": ["code_executor", "database_query", "file_operations"],
                "icon": "📊",
                "color": "#EF4444"
            }
        ]

    def create_agent(self, user_id: str, agent_data: Dict) -> Agent:
        """
        Create a new agent

        Args:
            user_id: User creating the agent
            agent_data: Agent configuration

        Returns:
            Created Agent object
        """
        # Validate config
        validated_data = validate_agent_config(agent_data)

        db = SessionLocal()
        try:
            agent = Agent(
                id=str(uuid4()),
                user_id=user_id,
                **validated_data
            )

            db.add(agent)
            db.commit()
            db.refresh(agent)

            return agent
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to create agent: {str(e)}")
        finally:
            db.close()

    def get_agent(self, agent_id: str, user_id: Optional[str] = None) -> Optional[Agent]:
        """
        Get agent by ID

        Args:
            agent_id: Agent ID
            user_id: Optional user ID for permission check

        Returns:
            Agent object or None
        """
        db = SessionLocal()
        try:
            query = db.query(Agent).filter(Agent.id == agent_id)

            # If user_id provided, only return if user owns it or it's public
            if user_id:
                query = query.filter(
                    or_(Agent.user_id == user_id, Agent.is_public == True)
                )

            return query.first()
        finally:
            db.close()

    def list_user_agents(self, user_id: str) -> List[Agent]:
        """Get all agents created by user"""
        db = SessionLocal()
        try:
            return db.query(Agent).filter(
                Agent.user_id == user_id
            ).order_by(Agent.created_at.desc()).all()
        finally:
            db.close()

    def list_public_agents(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Agent]:
        """
        List public agents (marketplace)

        Args:
            category: Filter by category
            tags: Filter by tags
            limit: Max results

        Returns:
            List of public Agent objects
        """
        db = SessionLocal()
        try:
            query = db.query(Agent).filter(Agent.is_public == True)

            if category:
                query = query.filter(Agent.category == category)

            # Order by rating and usage
            query = query.order_by(
                Agent.rating_average.desc(),
                Agent.usage_count.desc()
            )

            return query.limit(limit).all()
        finally:
            db.close()

    def update_agent(self, agent_id: str, user_id: str, updates: Dict) -> Agent:
        """
        Update agent configuration

        Args:
            agent_id: Agent ID
            user_id: User ID (must own agent)
            updates: Fields to update

        Returns:
            Updated Agent object
        """
        db = SessionLocal()
        try:
            agent = db.query(Agent).filter(
                Agent.id == agent_id,
                Agent.user_id == user_id
            ).first()

            if not agent:
                raise ValueError("Agent not found or access denied")

            # Validate updates
            validated_updates = validate_agent_config(updates)

            # Update fields
            for key, value in validated_updates.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)

            # Increment version
            agent.version += 1
            agent.updated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(agent)

            return agent
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to update agent: {str(e)}")
        finally:
            db.close()

    def delete_agent(self, agent_id: str, user_id: str) -> bool:
        """Delete agent (must own it)"""
        db = SessionLocal()
        try:
            agent = db.query(Agent).filter(
                Agent.id == agent_id,
                Agent.user_id == user_id
            ).first()

            if not agent:
                return False

            db.delete(agent)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to delete agent: {str(e)}")
        finally:
            db.close()

    def clone_agent(self, agent_id: str, user_id: str, new_name: Optional[str] = None) -> Agent:
        """
        Clone an existing agent

        Args:
            agent_id: Agent to clone
            user_id: User creating the clone
            new_name: Optional new name

        Returns:
            Cloned Agent object
        """
        db = SessionLocal()
        try:
            # Get original agent
            original = db.query(Agent).filter(
                Agent.id == agent_id,
                or_(Agent.user_id == user_id, Agent.is_template == True, Agent.is_public == True)
            ).first()

            if not original:
                raise ValueError("Agent not found or not cloneable")

            # Create clone
            clone_data = {
                "name": new_name or f"{original.name} (Copy)",
                "description": original.description,
                "category": original.category,
                "system_prompt": original.system_prompt,
                "model": original.model,
                "temperature": original.temperature,
                "max_tokens": original.max_tokens,
                "allowed_tools": original.allowed_tools,
                "guardrails": original.guardrails,
                "icon": original.icon,
                "color": original.color,
                "tags": original.tags
            }

            cloned_agent = self.create_agent(user_id, clone_data)
            cloned_agent.parent_agent_id = agent_id

            db.commit()
            db.refresh(cloned_agent)

            return cloned_agent
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to clone agent: {str(e)}")
        finally:
            db.close()

    def publish_agent(self, agent_id: str, user_id: str) -> Agent:
        """Publish agent to marketplace"""
        db = SessionLocal()
        try:
            agent = db.query(Agent).filter(
                Agent.id == agent_id,
                Agent.user_id == user_id
            ).first()

            if not agent:
                raise ValueError("Agent not found")

            agent.is_public = True
            agent.published_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(agent)

            return agent
        finally:
            db.close()

    def rate_agent(self, agent_id: str, user_id: str, rating: float, review: Optional[str] = None):
        """
        Rate an agent

        Args:
            agent_id: Agent to rate
            user_id: User rating
            rating: 1-5 stars
            review: Optional review text
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        db = SessionLocal()
        try:
            # Create or update rating
            existing_rating = db.query(AgentRating).filter(
                AgentRating.agent_id == agent_id,
                AgentRating.user_id == user_id
            ).first()

            if existing_rating:
                existing_rating.rating = rating
                existing_rating.review = review
            else:
                new_rating = AgentRating(
                    id=str(uuid4()),
                    agent_id=agent_id,
                    user_id=user_id,
                    rating=rating,
                    review=review
                )
                db.add(new_rating)

            # Update agent's average rating
            all_ratings = db.query(AgentRating).filter(
                AgentRating.agent_id == agent_id
            ).all()

            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                agent.rating_average = sum(r.rating for r in all_ratings) / len(all_ratings)
                agent.rating_count = len(all_ratings)

            db.commit()
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to rate agent: {str(e)}")
        finally:
            db.close()


# Singleton instance
agent_manager = AgentManager()
