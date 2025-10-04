from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON, Boolean
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

class WorkflowState(enum.Enum):
    """LALO workflow states matching the 5-step process"""
    INTERPRETING = "interpreting"      # Step 1: Semantic interpretation
    PLANNING = "planning"              # Step 2: Action plan creation
    BACKUP_VERIFY = "backup_verify"    # Step 3: Backup verification
    EXECUTING = "executing"            # Step 3: Plan execution
    REVIEWING = "reviewing"            # Step 4: Result review
    FINALIZING = "finalizing"          # Step 5: Final feedback
    COMPLETED = "completed"            # Complete
    ERROR = "error"                    # Error state

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

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    response_id = Column(String, nullable=False)
    helpful = Column(Boolean, default=None)
    reason = Column(String, nullable=True)
    details = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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

class WorkflowSession(Base):
    """
    Stores LALO workflow sessions with full context and state
    Tracks the 5-step LALO process for each user request
    """
    __tablename__ = "workflow_sessions"

    # Primary identification
    session_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Workflow state
    current_state = Column(Enum(WorkflowState), default=WorkflowState.INTERPRETING)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Request data
    original_request = Column(String, nullable=False)

    # Step 1: Interpretation data
    interpreted_intent = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    reasoning_trace = Column(JSON, nullable=True)  # List of reasoning steps
    suggested_clarifications = Column(JSON, nullable=True)  # List of clarification questions
    interpretation_approved = Column(Integer, default=0)  # 0=pending, 1=approved, -1=rejected

    # Step 2: Planning data
    action_plan = Column(JSON, nullable=True)  # The generated plan
    plan_confidence_score = Column(Float, nullable=True)
    plan_approved = Column(Integer, default=0)  # 0=pending, 1=approved, -1=rejected

    # Step 3: Backup data
    backup_id = Column(String, nullable=True)
    backup_verified = Column(Integer, default=0)

    # Step 3/4: Execution data
    execution_results = Column(JSON, nullable=True)  # Results from execution
    execution_steps_log = Column(JSON, nullable=True)  # Step-by-step log
    execution_success = Column(Integer, nullable=True)  # 0=failed, 1=success

    # Step 4/5: Review data
    review_feedback = Column(JSON, nullable=True)  # User's review feedback
    review_approved = Column(Integer, default=0)

    # Step 5: Final data
    final_feedback = Column(String, nullable=True)
    success_rating = Column(Float, nullable=True)  # 0.0 to 1.0

    # Feedback history (all interactions)
    feedback_history = Column(JSON, default=list)  # List of all feedback interactions

    # Error tracking
    error_message = Column(String, nullable=True)

    # Metadata
    model_metadata = Column(JSON, nullable=True)  # Models used for each step

    # Permanent memory flag
    committed_to_permanent_memory = Column(Integer, default=0)  # 0=no, 1=yes


class ToolExecution(Base):
    """
    Tracks individual tool executions for audit and learning
    """
    __tablename__ = "tool_executions"

    id = Column(String, primary_key=True)
    workflow_session_id = Column(String, ForeignKey("workflow_sessions.session_id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Tool information
    tool_name = Column(String, nullable=False)  # e.g., "web_search", "rag_query"
    tool_input = Column(JSON, nullable=False)  # Input parameters
    tool_output = Column(JSON, nullable=True)  # Tool results

    # Execution metadata
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="running")  # running, success, failed
    error_message = Column(String, nullable=True)

    # Resource usage
    execution_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)


class Agent(Base):
    """
    Custom AI agent definitions created by users
    """
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Agent configuration
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    system_prompt = Column(String, nullable=False)

    # Model configuration
    model = Column(String, default="gpt-4-turbo-preview")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)

    # Tool access
    allowed_tools = Column(JSON, default=list)  # List of tool names

    # Guardrails
    guardrails = Column(JSON, default=list)  # Safety rules

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_public = Column(Boolean, default=False)  # For marketplace
    version = Column(Integer, default=1)


class DataSource(Base):
    """
    Connected data sources (SharePoint, S3, databases, etc.)
    """
    __tablename__ = "data_sources"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Source configuration
    source_type = Column(String, nullable=False)  # sharepoint, s3, postgresql, etc.
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Connection details (encrypted)
    encrypted_credentials = Column(String, nullable=False)
    connection_config = Column(JSON, default=dict)

    # Indexing status
    indexed_at = Column(DateTime, nullable=True)
    documents_indexed = Column(Integer, default=0)
    index_status = Column(String, default="not_indexed")  # not_indexed, indexing, indexed, failed

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)


class AuditLog(Base):
    """
    Comprehensive audit trail for security and compliance
    """
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Event information
    event_type = Column(String, nullable=False)  # workflow_start, tool_use, agent_create, etc.
    action = Column(String, nullable=False)  # create, read, update, delete, execute
    resource_type = Column(String, nullable=False)  # workflow, agent, tool, data_source
    resource_id = Column(String, nullable=True)

    # Event details
    details = Column(JSON, default=dict)
    result = Column(String, nullable=False)  # success, failure
    error_message = Column(String, nullable=True)

    # Request metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class FeedbackEvent(Base):
    """
    Detailed feedback events for human-in-the-loop learning
    """
    __tablename__ = "feedback_events"

    id = Column(String, primary_key=True)
    workflow_session_id = Column(String, ForeignKey("workflow_sessions.session_id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Feedback context
    step = Column(String, nullable=False)  # interpretation, planning, execution, review
    feedback_type = Column(String, nullable=False)  # approve, reject, clarify, rating

    # Feedback content
    feedback_value = Column(String, nullable=True)  # The actual feedback
    rating = Column(Float, nullable=True)  # Numerical rating if applicable
    comments = Column(String, nullable=True)  # Free-text comments

    # Context at time of feedback
    ai_output = Column(JSON, nullable=True)  # What AI produced
    expected_output = Column(String, nullable=True)  # What user expected

    # Timestamp
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Create all tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
