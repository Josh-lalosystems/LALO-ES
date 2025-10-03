from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from database import User, Request, UsageRecord, RequestStatus

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, email: str) -> User:
        user = User(
            id=str(uuid.uuid4()),
            email=email
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_request(
        self,
        user_id: str,
        model: str,
        prompt: str
    ) -> Request:
        request = Request(
            id=str(uuid.uuid4()),
            user_id=user_id,
            model=model,
            prompt=prompt,
            status=RequestStatus.PENDING
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def update_request(
        self,
        request_id: str,
        status: RequestStatus,
        response: Optional[str] = None,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None,
        error: Optional[str] = None
    ) -> Request:
        request = self.db.query(Request).filter(Request.id == request_id).first()
        if request:
            if status == RequestStatus.COMPLETED:
                request.completed_at = datetime.utcnow()
            request.status = status
            if response is not None:
                request.response = response
            if tokens_used is not None:
                request.tokens_used = tokens_used
            if cost is not None:
                request.cost = cost
            if error is not None:
                request.error = error
            self.db.commit()
            self.db.refresh(request)
        return request

    def get_user_requests(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Request]:
        return self.db.query(Request)\
            .filter(Request.user_id == user_id)\
            .order_by(Request.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()

    def record_usage(
        self,
        user_id: str,
        model: str,
        tokens_used: int,
        cost: float
    ):
        today = datetime.utcnow().date()
        record = self.db.query(UsageRecord)\
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
            self.db.add(record)

        self.db.commit()

    def get_usage_stats(
        self,
        user_id: str,
        days: int = 30
    ):
        start_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(UsageRecord)\
            .filter(
                UsageRecord.user_id == user_id,
                UsageRecord.date >= start_date
            )\
            .order_by(UsageRecord.date.asc())\
            .all()
