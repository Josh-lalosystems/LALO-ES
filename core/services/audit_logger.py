from __future__ import annotations

from typing import Optional, Dict, List
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, JSON

from ..database import Base, engine, SessionLocal


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    user_id = Column(String, nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    resource = Column(String, nullable=True, index=True)
    level = Column(String, nullable=False, default="info")
    details = Column(JSON, nullable=True)


# Ensure table exists (will be formalized via Alembic later)
Base.metadata.create_all(bind=engine)


class AuditLoggerService:
    def record(self, action: str, user_id: Optional[str] = None, resource: Optional[str] = None, level: str = "info", details: Optional[Dict] = None) -> str:
        session = SessionLocal()
        try:
            log = AuditLog(
                id=str(uuid4()),
                user_id=user_id,
                action=action,
                resource=resource,
                level=level,
                details=details or {},
            )
            session.add(log)
            session.commit()
            return log.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list(self, limit: int = 100, offset: int = 0, user_id: Optional[str] = None, action: Optional[str] = None, level: Optional[str] = None) -> List[Dict]:
        session = SessionLocal()
        try:
            q = session.query(AuditLog).order_by(AuditLog.timestamp.desc())
            if user_id:
                q = q.filter(AuditLog.user_id == user_id)
            if action:
                q = q.filter(AuditLog.action == action)
            if level:
                q = q.filter(AuditLog.level == level)
            rows = q.offset(offset).limit(limit).all()
            return [
                {
                    "id": r.id,
                    "timestamp": (r.timestamp.isoformat() if r.timestamp else None),
                    "user_id": r.user_id,
                    "action": r.action,
                    "resource": r.resource,
                    "level": r.level,
                    "details": r.details or {},
                }
                for r in rows
            ]
        finally:
            session.close()


audit_logger = AuditLoggerService()
