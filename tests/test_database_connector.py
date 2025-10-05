"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import pytest
from connectors.database_connector import DatabaseConnector

def test_postgres(monkeypatch):
    class DummyConn:
        def cursor(self):
            class Cursor:
                def execute(self, sql):
                    pass
                def fetchall(self):
                    return [('table1',)]
            return Cursor()
    monkeypatch.setattr('psycopg2.connect', lambda **k: DummyConn())
    connector = DatabaseConnector({'db_type': 'postgres', 'pg_creds': {}})
    connector.connect()
    assert connector.test_connection() is True
    assert connector.sync()[0] == 'table1'
