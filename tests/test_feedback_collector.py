from core.services.feedback_collector import FeedbackCollector

def test_add_list_feedback():
    collector = FeedbackCollector()
    fb_id = collector.add_feedback('user1', 4.5, 1, 'UI', 'Great!')
    feedback = collector.list_feedback()
    assert any(f.id == fb_id for f in feedback)
