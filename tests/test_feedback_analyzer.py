from core.services.feedback_collector import FeedbackCollector
from core.services.feedback_analyzer import FeedbackAnalyzer

def test_sentiment_analysis():
    collector = FeedbackCollector()
    session = collector.session
    collector.add_feedback('user2', 5, 1, 'API', 'Amazing!')
    analyzer = FeedbackAnalyzer(session)
    results = analyzer.analyze_sentiment()
    assert any(r['sentiment'] > 0 for r in results)
