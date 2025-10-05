"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from connectors.base_connector import BaseConnector
from typing import Dict, Type

class ConnectorRegistry:
    """Registry for managing connector classes."""
    _registry: Dict[str, Type[BaseConnector]] = {}

    @classmethod
    def register(cls, name: str, connector_cls: Type[BaseConnector]):
        cls._registry[name] = connector_cls

    @classmethod
    def get_connector(cls, name: str) -> Type[BaseConnector]:
        return cls._registry.get(name)

    @classmethod
    def list_connectors(cls):
        return list(cls._registry.keys())
