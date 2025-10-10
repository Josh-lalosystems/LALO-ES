"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from ..database import User, Request, UsageRecord, RequestStatus, get_db, SessionLocal, Feedback, AuditLog

class DatabaseService:
    def __init__(self):
        """Initialize database service without storing session"""
        pass

    def get_session(self):
        """Get a new database session"""
        return SessionLocal()

    def create_user(self, email: str) -> User:
        """Create a new user with proper session management"""
        session = self.get_session()
        try:
            user = User(
                id=str(uuid.uuid4()),
                email=email
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID with proper session management"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()

    def create_request(
        self,
        user_id: str,
        model: str,
        prompt: str
    ) -> Request:
        """Create a new request with proper session management"""
        session = self.get_session()
        try:
            request = Request(
                id=str(uuid.uuid4()),
                user_id=user_id,
                model=model,
                prompt=prompt,
                status=RequestStatus.PENDING
            )
            session.add(request)
            session.commit()
            session.refresh(request)
            return request
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_request(
        self,
        request_id: str,
        status: RequestStatus,
        response: Optional[str] = None,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None,
        error: Optional[str] = None
    ) -> Request:
        """Update request with proper session management"""
        session = self.get_session()
        try:
            request = session.query(Request).filter(Request.id == request_id).first()
            if request:
                if status == RequestStatus.COMPLETED:
                    request.completed_at = datetime.now(timezone.utc)
                request.status = status
                if response is not None:
                    request.response = response
                if tokens_used is not None:
                    request.tokens_used = tokens_used
                if cost is not None:
                    request.cost = cost
                if error is not None:
                    request.error = error
                session.commit()
                session.refresh(request)
            return request
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_user_requests(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Request]:
        """Get user requests with proper session management"""
        session = self.get_session()
        try:
            return session.query(Request)\
                .filter(Request.user_id == user_id)\
                .order_by(Request.created_at.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
        finally:
            session.close()

    def record_usage(
        self,
        user_id: str,
        model: str,
        tokens_used: int,
        cost: float
    ):
        """Record usage with proper session management"""
        session = self.get_session()
        try:
            today = datetime.now(timezone.utc).date()
            record = session.query(UsageRecord)\
                .filter(
                    UsageRecord.user_id == user_id,
                    UsageRecord.model == model,
                    func.date(UsageRecord.date) == today
                ).first()

            if record:
                record.tokens_used += tokens_used
                record.requests_count += 1
                record.cost += cost
            else:
                record = UsageRecord(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    date=today,
                    model=model,
                    tokens_used=tokens_used,
                    requests_count=1,
                    cost=cost
                )
                session.add(record)

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_usage_stats(
        self,
        user_id: str,
        days: int = 30
    ):
        """Get usage statistics with proper session management"""
        session = self.get_session()
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            return session.query(UsageRecord)\
                .filter(
                    UsageRecord.user_id == user_id,
                    UsageRecord.date >= start_date
                )\
                .order_by(UsageRecord.date.asc())\
                .all()
        finally:
            session.close()

    def save_feedback(self, user_id: str, response_id: str, helpful: bool, reason: str | None = None, details: str | None = None):
        """Persist a feedback record."""
        session = self.get_session()
        try:
            fb = Feedback(
                id=str(uuid.uuid4()),
                user_id=user_id,
                response_id=response_id,
                helpful=helpful,
                reason=reason,
                details=details,
            )
            session.add(fb)
            session.commit()
            return fb
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def record_fallback_telemetry(self, user_id: str, prompt: str, primary_model: str, attempts: list):
        """
        Record fallback attempts as an audit log entry for later analysis.

        attempts: list of dicts with keys: model, success, confidence, error (optional)
        """
        session = self.get_session()
        try:
            log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                event_type="fallback_attempts",
                action="record",
                resource_type="model_selection",
                resource_id=primary_model,
                details={"prompt_excerpt": (prompt or '')[:400], "attempts": attempts},
                result="success"
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    def attach_fallbacks_to_request(self, request_id: str, attempts: list):
        """
        Attach fallback_attempts metadata to an existing Request row.
        Safe to call after create_request/update_request; will open its own session.
        """
        session = self.get_session()
        try:
            req = session.query(Request).filter(Request.id == request_id).first()
            if not req:
                return None
            req.fallback_attempts = attempts
            session.commit()
            session.refresh(req)
            return req
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# Create a global database service instance
# No session stored - creates new sessions per operation
database_service = DatabaseService()
