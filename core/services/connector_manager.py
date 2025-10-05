"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from connectors.connector_registry import ConnectorRegistry
from connectors.base_connector import BaseConnector
from typing import Dict, Any

class ConnectorManager:
    """Manages connector instances and lifecycle."""
    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}

    def add_connector(self, name: str, config: dict):
        connector_cls = ConnectorRegistry.get_connector(name)
        if not connector_cls:
            raise ValueError(f"Connector '{name}' not found")
        instance = connector_cls(config)
        self.connectors[name] = instance
        return instance

    def get_connector(self, name: str):
        return self.connectors.get(name)

    def list_connectors(self):
        return list(self.connectors.keys())

    def test_connector(self, name: str):
        connector = self.get_connector(name)
        return connector.test_connection() if connector else False

    def sync_connector(self, name: str):
        connector = self.get_connector(name)
        return connector.sync() if connector else None
