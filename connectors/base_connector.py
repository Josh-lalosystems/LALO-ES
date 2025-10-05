"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

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
