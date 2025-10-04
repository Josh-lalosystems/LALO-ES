from core.services.feedback_collector import FeedbackCollector
from core.services.learning_engine import LearningEngine

def test_learning_engine():
    collector = FeedbackCollector()
    session = collector.session
    collector.add_feedback('user3', 5, 1, 'Performance', 'Fast and reliable')
    engine = LearningEngine(session)
    examples = engine.collect_examples()
    assert any(f.rating >= 4 for f in examples)
    assert engine.optimize_prompt() == "Optimized prompt"
    ab = engine.ab_test()
    assert ab['A'] < ab['B']
