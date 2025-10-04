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
