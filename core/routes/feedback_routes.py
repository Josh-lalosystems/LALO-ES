from fastapi import APIRouter
from core.services.feedback_collector import FeedbackCollector

router = APIRouter()
collector = FeedbackCollector()

@router.post('/api/feedback')
def add_feedback(payload: dict):
    user_id = payload.get('user_id')
    rating = payload.get('rating')
    thumbs = payload.get('thumbs')
    category = payload.get('category')
    comments = payload.get('comments')
    fb_id = collector.add_feedback(user_id, rating, thumbs, category, comments)
    return {"id": fb_id}

@router.get('/api/feedback')
def list_feedback():
    feedback = collector.list_feedback()
    return [{"id": f.id, "user_id": f.user_id, "rating": f.rating, "thumbs": f.thumbs, "category": f.category, "comments": f.comments, "created_at": f.created_at.isoformat()} for f in feedback]
