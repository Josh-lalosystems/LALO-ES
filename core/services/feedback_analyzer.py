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
