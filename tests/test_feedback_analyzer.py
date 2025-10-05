"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from core.services.feedback_collector import FeedbackCollector
from core.services.feedback_analyzer import FeedbackAnalyzer

def test_sentiment_analysis():
    collector = FeedbackCollector()
    session = collector.session
    collector.add_feedback('user2', 5, 1, 'API', 'Amazing!')
    analyzer = FeedbackAnalyzer(session)
    results = analyzer.analyze_sentiment()
    assert any(r['sentiment'] > 0 for r in results)
