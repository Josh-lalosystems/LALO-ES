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
