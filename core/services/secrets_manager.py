"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from __future__ import annotations

from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime, timezone
import os
import json
from cryptography.fernet import Fernet

from ..database import SessionLocal, engine

# Lightweight secrets store table using the same DB without requiring immediate Alembic migration.
# We store secrets in a dedicated table 'secrets_store' if it exists. If not, we fall back to a JSON blob row.
# To avoid schema drift, this module uses an internal table creation on first use.

from sqlalchemy import Table, Column, String, DateTime, Integer, MetaData, create_engine, inspect
from sqlalchemy.exc import OperationalError


ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate ephemeral key if missing; warn in logs. For production, always set ENCRYPTION_KEY.
    ENCRYPTION_KEY = Fernet.generate_key().decode()
fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)


class SecretsManager:
    """
    Encrypted Secrets Manager

    - Stores per-user or global secrets with envelope encryption (Fernet symmetric key)
    - Provides CRUD operations; values are always encrypted at rest
    - Returns plaintext only on explicit get() calls; avoids logging secrets
    """

    def __init__(self):
        self._engine = engine
        self._metadata = MetaData()
        self._table = self._ensure_table()

    def _ensure_table(self):
        inspector = inspect(self._engine)
        tables = inspector.get_table_names()
        if 'secrets_store' not in tables:
            # Create table dynamically
            table = Table(
                'secrets_store',
                self._metadata,
                Column('id', String, primary_key=True),
                Column('name', String, nullable=False),
                Column('user_id', String, nullable=True),
                Column('value_encrypted', String, nullable=False),
                Column('version', Integer, nullable=False, default=1),
                Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc)),
                Column('updated_at', DateTime, default=lambda: datetime.now(timezone.utc)),
            )
            self._metadata.create_all(self._engine, tables=[table])
            return table
        else:
            return Table('secrets_store', self._metadata, autoload_with=self._engine)

    def _encrypt(self, value: str) -> str:
        return fernet.encrypt(value.encode()).decode()

    def _decrypt(self, value_encrypted: str) -> str:
        return fernet.decrypt(value_encrypted.encode()).decode()

    def set_secret(self, name: str, value: str, user_id: Optional[str] = None) -> Dict:
        """Create or update a secret. Returns metadata (no plaintext)."""
        now = datetime.now(timezone.utc)
        enc = self._encrypt(value)
        session = SessionLocal()
        try:
            # Upsert by (name, user_id)
            row = session.execute(
                self._table.select().where(
                    (self._table.c.name == name) & (self._table.c.user_id == user_id)
                )
            ).fetchone()
            if row:
                version = int(row.version or 1) + 1
                session.execute(
                    self._table.update()
                    .where((self._table.c.name == name) & (self._table.c.user_id == user_id))
                    .values(value_encrypted=enc, version=version, updated_at=now)
                )
                secret_id = row.id
            else:
                secret_id = f"sec_{int(now.timestamp()*1000)}"
                session.execute(
                    self._table.insert().values(
                        id=secret_id,
                        name=name,
                        user_id=user_id,
                        value_encrypted=enc,
                        version=1,
                        created_at=now,
                        updated_at=now,
                    )
                )
            session.commit()
            return {
                'id': secret_id,
                'name': name,
                'user_id': user_id,
                'version': (version if row else 1),
                'updated_at': now.isoformat(),
            }
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_secret(self, name: str, user_id: Optional[str] = None) -> Optional[str]:
        """Return decrypted value or None if not found."""
        session = SessionLocal()
        try:
            row = session.execute(
                self._table.select().where(
                    (self._table.c.name == name) & (self._table.c.user_id == user_id)
                )
            ).fetchone()
            if not row:
                return None
            return self._decrypt(row.value_encrypted)
        finally:
            session.close()

    def delete_secret(self, name: str, user_id: Optional[str] = None) -> bool:
        session = SessionLocal()
        try:
            result = session.execute(
                self._table.delete().where(
                    (self._table.c.name == name) & (self._table.c.user_id == user_id)
                )
            )
            session.commit()
            return result.rowcount > 0  # type: ignore
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_secrets(self, user_id: Optional[str] = None) -> List[Dict]:
        """List secret metadata (no values)."""
        session = SessionLocal()
        try:
            sel = self._table.select()
            if user_id is not None:
                sel = sel.where(self._table.c.user_id == user_id)
            rows = session.execute(sel).fetchall()
            return [
                {
                    'id': r.id,
                    'name': r.name,
                    'user_id': r.user_id,
                    'version': r.version,
                    'created_at': (r.created_at.isoformat() if r.created_at else None),
                    'updated_at': (r.updated_at.isoformat() if r.updated_at else None),
                }
                for r in rows
            ]
        finally:
            session.close()


# Global instance
secrets_manager = SecretsManager()
