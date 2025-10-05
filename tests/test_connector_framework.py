"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import pytest
from connectors.base_connector import BaseConnector
from connectors.connector_registry import ConnectorRegistry

class DummyConnector(BaseConnector):
    def connect(self):
        return True
    def test_connection(self):
        return True
    def sync(self):
        return True

ConnectorRegistry.register('dummy', DummyConnector)

def test_registry():
    assert 'dummy' in ConnectorRegistry.list_connectors()
    connector_cls = ConnectorRegistry.get_connector('dummy')
    assert issubclass(connector_cls, BaseConnector)
    instance = connector_cls(config={})
    assert instance.connect() is True
    assert instance.test_connection() is True
    assert instance.sync() is True
