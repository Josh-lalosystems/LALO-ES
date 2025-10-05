"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from core.models.feedback import Feedback
from sqlalchemy.orm import Session
from textblob import TextBlob

class FeedbackAnalyzer:
    def __init__(self, session: Session):
        self.session = session

    def analyze_sentiment(self):
        feedback = self.session.query(Feedback).all()
        results = []
        for f in feedback:
            tb = TextBlob(f.comments or "")
            results.append({"id": f.id, "sentiment": tb.sentiment.polarity})
        return results
