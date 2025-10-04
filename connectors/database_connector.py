from connectors.base_connector import BaseConnector
import psycopg2
import pymysql
import pyodbc

class DatabaseConnector(BaseConnector):
    def connect(self):
        db_type = self.config.get('db_type')
        if db_type == 'postgres':
            self.conn = psycopg2.connect(**self.config.get('pg_creds', {}))
        elif db_type == 'mysql':
            self.conn = pymysql.connect(**self.config.get('mysql_creds', {}))
        elif db_type == 'mssql':
            self.conn = pyodbc.connect(self.config.get('odbc_conn_str'))
        else:
            raise ValueError('Unknown db_type')
        return True

    def test_connection(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT 1')
            return True
        except Exception:
            return False

    def sync(self):
        # Example: List tables
        cursor = self.conn.cursor()
        db_type = self.config.get('db_type')
        if db_type == 'postgres':
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            return [row[0] for row in cursor.fetchall()]
        elif db_type == 'mysql':
            cursor.execute("SHOW TABLES")
            return [row[0] for row in cursor.fetchall()]
        elif db_type == 'mssql':
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES")
            return [row[0] for row in cursor.fetchall()]
        return []
