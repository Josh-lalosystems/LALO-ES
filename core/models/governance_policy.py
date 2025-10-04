from sqlalchemy import Column, String, DateTime, JSON, Boolean
from datetime import datetime, timezone

from ..database import Base, engine


class GovernancePolicy(Base):
    __tablename__ = "governance_policies"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    enabled = Column(Boolean, default=True)
    # Simple policy doc structure, e.g. { "deny_categories": ["code_execution"], "require_perms": {"external_api_access": true} }
    rules = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Ensure table exists
Base.metadata.create_all(bind=engine)
