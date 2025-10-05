"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from core.services.feedback_collector import FeedbackCollector

def test_add_list_feedback():
    collector = FeedbackCollector()
    fb_id = collector.add_feedback('user1', 4.5, 1, 'UI', 'Great!')
    feedback = collector.list_feedback()
    assert any(f.id == fb_id for f in feedback)
