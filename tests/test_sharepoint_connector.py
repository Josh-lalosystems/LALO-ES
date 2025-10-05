"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import pytest
from connectors.sharepoint_connector import SharePointConnector

def test_sharepoint_connector(monkeypatch):
    class DummyAccount:
        def is_authenticated(self):
            return True
        def authenticate(self, scopes=None):
            return True
        def sharepoint(self):
            class SharePoint:
                def get_sites(self):
                    class Site:
                        def get_default_drive(self):
                            class Drive:
                                def get_items(self):
                                    class Item:
                                        name = 'doc1'
                                    return [Item()]
                            return Drive()
                    return [Site()]
            return SharePoint()
    import connectors.sharepoint_connector
    monkeypatch.setattr(connectors.sharepoint_connector, 'Account', lambda creds: DummyAccount())
    connector = SharePointConnector({'client_id': 'dummy', 'client_secret': 'dummy'})
    assert connector.connect() is True
    assert connector.test_connection() is True
    assert isinstance(connector.sync(), list)
