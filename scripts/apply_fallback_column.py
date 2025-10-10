"""
Standalone helper to add `fallback_attempts` JSON column to `requests` table if it doesn't exist.
This is a lightweight fallback for environments where Alembic isn't run.

Usage:
  python scripts/apply_fallback_column.py
"""
import sqlite3
import os
from pathlib import Path
import json

DB = os.getenv('DATABASE_URL', 'sqlite:///./lalo.db')

def sqlite_path_from_url(url: str) -> str:
    if url.startswith('sqlite:///'):
        return url.replace('sqlite:///', '')
    raise ValueError('Only sqlite:/// URLs supported by this helper')

def ensure_column():
    dbpath = sqlite_path_from_url(DB)
    conn = sqlite3.connect(dbpath)
    try:
        cur = conn.cursor()
        # Check if column exists
        cur.execute("PRAGMA table_info(requests)")
        cols = [r[1] for r in cur.fetchall()]
        if 'fallback_attempts' in cols:
            print('Column fallback_attempts already present')
            return
        # Add column (nullable)
        cur.execute('ALTER TABLE requests ADD COLUMN fallback_attempts JSON')
        conn.commit()
        print('Added fallback_attempts column to requests')
    except Exception as e:
        print('Failed to add column:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    ensure_column()
