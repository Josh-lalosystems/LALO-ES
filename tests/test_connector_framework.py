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
