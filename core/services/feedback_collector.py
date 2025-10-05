"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from core.models.feedback import Feedback, Base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

engine = create_engine('sqlite:///lalo.db')
Base.metadata.create_all(engine)

class FeedbackCollector:
    def __init__(self):
        self.session = Session(bind=engine)

    def add_feedback(self, user_id, rating, thumbs, category, comments):
        fb = Feedback(user_id=user_id, rating=rating, thumbs=thumbs, category=category, comments=comments)
        self.session.add(fb)
        self.session.commit()
        return fb.id

    def list_feedback(self):
        return self.session.query(Feedback).all()
