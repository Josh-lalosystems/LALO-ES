# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Module: AgentFactory
Purpose: Dynamically instantiate agent instances based on enterprise context:
         (region, system_type, role). This aligns with LALO's unique IP
         around context-aware agent creation logic.

Dependencies:
  - ConfigRegistry: maps tuples → Agent classes
  - AgentRegistry: tracks active agents
  - uuid for unique agent IDs

Edge cases handled:
  - Missing mapping: fallback to DefaultAgent
  - Invalid UserContext: validated early
  - UUID collisions: checked by registry
"""

import uuid
from .config_registry import ConfigRegistry
from .agent_registry import AgentRegistry
from .agents.default_agent import DefaultAgent

class AgentCreationError(Exception):
    pass

class AgentFactory:
    def __init__(self, config: ConfigRegistry, registry: AgentRegistry):
        """
        config: instance of ConfigRegistry
                provides mapping (region, system_type, role) → Agent class
        registry: in-memory or persistent registry to track agents
        """
        self.config = config
        self.registry = registry

    def create_agent(self, user_request: dict, user_context: dict):
        """
        Create an agent tailored to the given context and request.
        - user_context must include: 'region', 'system_type', 'role'
        - Raises AgentCreationError on invalid inputs or UUID collision
        - Logs fallback to DefaultAgent when needed
        """
        # Validate context object
        if not all(k in user_context for k in ('region', 'system_type', 'role')):
            raise AgentCreationError("UserContext missing required keys")

        key = (user_context['region'], user_context['system_type'], user_context['role'])
        AgentClass = self.config.get(key, DefaultAgent)
        agent = AgentClass(request=user_request, context=user_context)

        # Assign unique ID
        agent.id = str(uuid.uuid4())
        if self.registry.exists(agent.id):
            raise AgentCreationError(f"UUID collision for agent id {agent.id}")

        self.registry.register(agent.id, agent)
        return agent
