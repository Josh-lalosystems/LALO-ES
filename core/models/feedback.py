from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Feedback(Base):
    __tablename__ = 'feedback'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    rating = Column(Float)
    thumbs = Column(Integer)
    category = Column(String)
    comments = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
