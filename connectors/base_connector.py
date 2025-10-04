from abc import ABC, abstractmethod

class BaseConnector(ABC):
    """Abstract base class for all data connectors."""
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        pass

    @abstractmethod
    def sync(self):
        pass
