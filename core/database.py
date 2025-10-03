from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
import enum
import os
import json
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

# Initialize encryption for API keys
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY") or Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

# Database configuration
DATABASE_URL = "sqlite:///./lalo.db"

# Configure the database engine (without pooling for SQLite)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

class RequestStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    requests = relationship("Request", back_populates="user")
    usage_records = relationship("UsageRecord", back_populates="user")

class Request(Base):
    __tablename__ = "requests"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    model = Column(String, nullable=False)
    prompt = Column(String, nullable=False)
    response = Column(String)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    tokens_used = Column(Integer)
    cost = Column(Float)
    error = Column(String)

    # Relationships
    user = relationship("User", back_populates="requests")

class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    date = Column(DateTime, nullable=False)
    model = Column(String, nullable=False)
    tokens_used = Column(Integer, default=0)
    requests_count = Column(Integer, default=0)
    cost = Column(Float, default=0.0)

    # Relationships
    user = relationship("User", back_populates="usage_records")

class APIKeys(Base):
    __tablename__ = "api_keys"
    
    user_id = Column(String, primary_key=True)
    encrypted_keys = Column(String)
    
    @property
    def keys(self) -> dict:
        if not self.encrypted_keys:
            return {}
        decrypted = fernet.decrypt(self.encrypted_keys.encode())
        return json.loads(decrypted)
    
    @keys.setter
    def keys(self, value: dict):
        encrypted = fernet.encrypt(json.dumps(value).encode())
        self.encrypted_keys = encrypted.decode()

# Create all tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
