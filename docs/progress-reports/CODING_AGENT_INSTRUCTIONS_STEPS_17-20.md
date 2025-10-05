# Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of LALO AI Platform and is protected by copyright law.
# Unauthorized copying, modification, distribution, or use of this software,
# via any medium, is strictly prohibited without the express written permission
# of LALO AI SYSTEMS, LLC.
#

# Coding Agent Instructions: Steps 17-20 Implementation

## ⚠️ CRITICAL RULES - READ FIRST

### Git Branch Management
1. **DO NOT create any new branches**
2. **DO NOT checkout any branches**
3. **DO NOT switch branches for any reason**
4. **STAY ON CURRENT BRANCH:** `cf/phase3-frontend-ux`
5. **DO NOT use git checkout, git branch -b, or any branch switching commands**
6. If you need to commit: Use `git add` and `git commit` ONLY (no branch operations)

### Git Remote Management
1. **DO NOT create any new git remotes**
2. **DO NOT modify existing remotes**
3. **ONLY use the existing `origin` remote**
4. If pushing is needed: Use `git push origin cf/phase3-frontend-ux` (current branch only)

### File Operations
1. **DO NOT delete or modify any existing tool files in `core/tools/`**
2. **DO NOT modify `core/tools/__init__.py` unless specifically adding new imports**
3. **CREATE NEW FILES ONLY for Steps 17-20 requirements**
4. All new files should follow existing patterns and conventions

### Verification Before Starting
1. Confirm current branch is `cf/phase3-frontend-ux`
2. Verify `core/tools/` has 10 .py files
3. Check that all imports are working
4. Run: `python -c "import logging; logging.basicConfig(level=logging.INFO); from core.tools import tool_registry; logging.getLogger('lalo.docs').info(len(tool_registry.get_all_tools()))"`
   - Expected output: 7 (the number of registered tools)

---

## Project Context

### What's Already Complete (DO NOT MODIFY)
- ✅ Steps 1-7: Core workflow engine (semantic interpreter, action planner, tool executor, orchestrator)
- ✅ Steps 8-12: Workflow routes, 4 core tools (web_search, rag_query, image_generator, code_executor)
- ✅ Steps 13-16: Additional tools (file_operations, database_query, api_call) + Tool Settings UI
- ✅ Total tools: 7 tools fully operational
- ✅ Database: 11 tables (Users, WorkflowSessions, ToolExecutions, etc.)
- ✅ All services running on ports: 8000 (main), 8101 (RTI), 8102 (MCP), 8103 (Creation)

### Current System Architecture
```
LALO AI Platform
├── Backend (FastAPI on port 8000)
│   ├── Workflow Orchestrator (5-step LALO process)
│   ├── Tool Registry (7 tools registered)
│   ├── Authentication (JWT + demo mode)
│   ├── API Key Management (encrypted)
│   └── Database (SQLite with 11 tables)
├── Microservices
│   ├── RTI Service (port 8101)
│   ├── MCP Service (port 8102)
│   └── Creation Service (port 8103)
└── Frontend (React + Material-UI)
    └── Components (Login, Settings, Admin/ToolSettings)
```

---

## YOUR TASK: Implement Steps 17-20

### Step 17: Role-Based Access Control (RBAC)
**Time Estimate:** 2-3 hours
**Priority:** HIGH

#### Requirements:
1. **Define 3 Roles:**
   - `Admin` - Full system access
   - `User` - Can execute workflows, use tools
   - `Viewer` - Read-only access

2. **Define Permissions:**
   - `execute_workflow` - Can start workflows
   - `create_agent` - Can create custom agents
   - `manage_users` - Can add/remove users (admin only)
   - `view_audit_logs` - Can view audit logs
   - `manage_tools` - Can enable/disable tools (admin only)
   - `use_tool:web_search`, `use_tool:rag_query`, etc. (per-tool permissions)

3. **Implementation Files to Create:**

**File 1: `core/models/rbac.py`**
```python
from enum import Enum
from sqlalchemy import Column, String, JSON, Boolean, ForeignKey
from .database import Base

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class Permission(str, Enum):
    EXECUTE_WORKFLOW = "execute_workflow"
    CREATE_AGENT = "create_agent"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_TOOLS = "manage_tools"
    USE_TOOL_WEB_SEARCH = "use_tool:web_search"
    USE_TOOL_RAG = "use_tool:rag_query"
    # ... add all tool permissions

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(String, nullable=False)  # Role enum value
    granted_by = Column(String, nullable=True)
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(String, primary_key=True)
    role = Column(String, nullable=False)
    permission = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
```

**File 2: `core/services/rbac.py`**
```python
from typing import List, Optional
from core.models.rbac import Role, Permission, UserRole, RolePermission
from core.database import SessionLocal

class RBACService:
    """Role-Based Access Control Service"""

    def __init__(self):
        self._role_permissions = self._load_default_permissions()

    def _load_default_permissions(self) -> dict:
        """Define default role permissions"""
        return {
            Role.ADMIN: [p.value for p in Permission],  # All permissions
            Role.USER: [
                Permission.EXECUTE_WORKFLOW.value,
                Permission.USE_TOOL_WEB_SEARCH.value,
                Permission.USE_TOOL_RAG.value,
                # ... user permissions
            ],
            Role.VIEWER: [
                Permission.VIEW_AUDIT_LOGS.value,
            ]
        }

    def assign_role(self, user_id: str, role: Role, granted_by: str) -> bool:
        """Assign role to user"""
        # Implementation
        pass

    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has permission"""
        # Implementation
        pass

    def get_user_roles(self, user_id: str) -> List[Role]:
        """Get all roles for a user"""
        # Implementation
        pass

    def get_user_permissions(self, user_id: str) -> List[Permission]:
        """Get all permissions for a user"""
        # Implementation
        pass

# Singleton
rbac_service = RBACService()
```

**File 3: `core/middleware/auth_middleware.py`**
```python
from fastapi import Request, HTTPException, status
from core.services.rbac import rbac_service, Permission

def require_permission(permission: Permission):
    """Decorator to check permission"""
    async def permission_checker(request: Request):
        user_id = request.state.user_id  # Set by auth middleware
        if not rbac_service.check_permission(user_id, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission.value}"
            )
        return True
    return permission_checker
```

**File 4: `lalo-frontend/src/components/admin/UserRoles.tsx`**
- Create UI to view users and their roles
- Add/remove role assignments
- Show permission matrix

4. **Update Database:**
   - Run `alembic revision --autogenerate -m "Add RBAC tables"`
   - Run `alembic upgrade head`

5. **Update Routes:**
   - Add permission checks to workflow routes
   - Add permission checks to tool execution
   - Example: `@router.post("/workflow/start", dependencies=[Depends(require_permission(Permission.EXECUTE_WORKFLOW))])`

---

### Step 18: Audit Logging
**Time Estimate:** 1-2 hours
**Priority:** HIGH

#### Requirements:

**File 1: `core/services/audit_logger.py`**
```python
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, JSON, DateTime
from core.database import Base, SessionLocal
from uuid import uuid4

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)  # "workflow_start", "tool_execute", etc.
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=True)  # "workflow", "tool", "user"
    resource_id = Column(String, nullable=True)
    details = Column(JSON, default=dict)
    result = Column(String, nullable=False)  # "success", "failure", "unauthorized"
    error_message = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class AuditLogger:
    """Centralized audit logging service"""

    def log_event(
        self,
        user_id: str,
        event_type: str,
        action: str,
        result: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log an audit event"""
        db = SessionLocal()
        try:
            log = AuditLog(
                user_id=user_id,
                event_type=event_type,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                result=result,
                error_message=error_message,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(log)
            db.commit()
        except Exception as e:
            db.rollback()
            # Log to console if DB fails
            print(f"AUDIT LOG FAILED: {e}")
        finally:
            db.close()

    def get_logs(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Retrieve audit logs"""
        # Implementation
        pass

# Singleton
audit_logger = AuditLogger()
```

**File 2: `lalo-frontend/src/components/admin/AuditLogs.tsx`**
- Display audit logs in a table
- Filter by user, event type, date range
- Export logs to CSV
- Pagination

**Integration Points:**
1. Add audit logging to workflow routes:
   ```python
   @router.post("/workflow/start")
   async def start_workflow(...):
       audit_logger.log_event(
           user_id=current_user,
           event_type="workflow_start",
           action="start_workflow",
           result="success",
           resource_type="workflow",
           resource_id=session_id,
           details={"request": request.user_request}
       )
   ```

2. Add to tool execution (in `tool_executor.py`)
3. Add to authentication events
4. Add to permission checks

---

### Step 19: Data Governance Policies
**Time Estimate:** 2-3 hours
**Priority:** MEDIUM

#### Requirements:

**File 1: `core/models/governance_policy.py`**
```python
from enum import Enum

class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class DataPolicy(Base):
    __tablename__ = "data_policies"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    classification = Column(String, nullable=False)
    access_rules = Column(JSON, default=dict)
    retention_days = Column(Integer, nullable=True)
    masking_enabled = Column(Boolean, default=False)
    masking_rules = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

**File 2: `core/services/data_governor.py`**
```python
import re
from typing import Optional, List, Dict

class DataGovernor:
    """Data governance and compliance service"""

    def __init__(self):
        self.pii_patterns = self._load_pii_patterns()

    def _load_pii_patterns(self) -> Dict[str, str]:
        """PII detection regex patterns"""
        return {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        }

    def detect_pii(self, text: str) -> List[str]:
        """Detect PII in text"""
        detected = []
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, text):
                detected.append(pii_type)
        return detected

    def mask_pii(self, text: str) -> str:
        """Mask PII in text"""
        masked = text
        for pii_type, pattern in self.pii_patterns.items():
            masked = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", masked)
        return masked

    def check_data_access(
        self,
        user_id: str,
        classification: DataClassification
    ) -> bool:
        """Check if user can access data of given classification"""
        # Implementation with RBAC integration
        pass

    def apply_retention_policy(self, resource_id: str):
        """Apply data retention policy"""
        # Implementation
        pass

# Singleton
data_governor = DataGovernor()
```

**Integration:**
1. Add PII detection to tool inputs/outputs
2. Apply masking to audit logs if needed
3. Add data classification to stored data

---

### Step 20: Secrets Management
**Time Estimate:** 1-2 hours
**Priority:** HIGH

#### Requirements:

**File: `core/services/secrets_manager.py`**
```python
from cryptography.fernet import Fernet
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

class SecretsManager:
    """Enhanced secrets management with rotation"""

    def __init__(self):
        self.master_key = os.getenv("MASTER_ENCRYPTION_KEY")
        if not self.master_key:
            # Generate if not exists (dev only)
            self.master_key = Fernet.generate_key().decode()
        self.fernet = Fernet(self.master_key.encode())
        self._rotation_days = 90  # Rotate secrets every 90 days

    def encrypt_secret(self, secret: str, metadata: Optional[dict] = None) -> dict:
        """Encrypt a secret with metadata"""
        encrypted = self.fernet.encrypt(secret.encode()).decode()
        return {
            "encrypted_value": encrypted,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "rotation_due": (datetime.now(timezone.utc) + timedelta(days=self._rotation_days)).isoformat(),
            "metadata": metadata or {}
        }

    def decrypt_secret(self, encrypted_data: dict) -> str:
        """Decrypt a secret"""
        encrypted_value = encrypted_data["encrypted_value"]
        return self.fernet.decrypt(encrypted_value.encode()).decode()

    def needs_rotation(self, encrypted_data: dict) -> bool:
        """Check if secret needs rotation"""
        rotation_due = datetime.fromisoformat(encrypted_data["rotation_due"])
        return datetime.now(timezone.utc) > rotation_due

    def rotate_secret(self, old_encrypted_data: dict, new_secret: str) -> dict:
        """Rotate a secret"""
        metadata = old_encrypted_data.get("metadata", {})
        metadata["rotated_from"] = old_encrypted_data["created_at"]
        metadata["rotation_count"] = metadata.get("rotation_count", 0) + 1
        return self.encrypt_secret(new_secret, metadata)

    def log_secret_access(self, user_id: str, secret_id: str, action: str):
        """Log secret access for audit"""
        from core.services.audit_logger import audit_logger
        audit_logger.log_event(
            user_id=user_id,
            event_type="secret_access",
            action=action,
            result="success",
            resource_type="secret",
            resource_id=secret_id
        )

# Singleton
secrets_manager = SecretsManager()
```

**Integration:**
1. Update `key_management.py` to use `secrets_manager` instead of direct Fernet
2. Add rotation reminders to admin UI
3. Log all secret access events

---

## Implementation Order

1. **Step 20 FIRST** (Secrets Management) - 1-2 hours
   - This is foundational and doesn't depend on others
   - Update existing key management to use it

2. **Step 17** (RBAC) - 2-3 hours
   - Needed for proper access control
   - Integrates with audit logging

3. **Step 18** (Audit Logging) - 1-2 hours
   - Requires RBAC for permission logging
   - Provides compliance trail

4. **Step 19** (Data Governance) - 2-3 hours
   - Uses RBAC for access checks
   - Uses audit logging for compliance

**Total Time: 6-10 hours**

---

## Testing Requirements

For each step, create a test file:

**File: `tests/test_rbac.py`**
```python
import pytest
from core.services.rbac import rbac_service, Role, Permission

def test_assign_role():
    result = rbac_service.assign_role("user123", Role.USER, "admin")
    assert result is True

def test_check_permission():
    rbac_service.assign_role("user123", Role.USER, "admin")
    assert rbac_service.check_permission("user123", Permission.EXECUTE_WORKFLOW) is True
    assert rbac_service.check_permission("user123", Permission.MANAGE_USERS) is False
```

Create similar test files for:
- `tests/test_audit_logger.py`
- `tests/test_data_governor.py`
- `tests/test_secrets_manager.py`

---

## Database Migrations

After creating all models, run:
```bash
alembic revision --autogenerate -m "Add RBAC, audit logs, and governance tables"
alembic upgrade head
```

---

## Deliverables Checklist

### Step 17 - RBAC ✓
- [ ] `core/models/rbac.py` - Role and permission models
- [ ] `core/services/rbac.py` - RBAC service implementation
- [ ] `core/middleware/auth_middleware.py` - Permission checking middleware
- [ ] `lalo-frontend/src/components/admin/UserRoles.tsx` - Role management UI
- [ ] Database migration for RBAC tables
- [ ] Tests in `tests/test_rbac.py`
- [ ] Updated workflow routes with permission checks

### Step 18 - Audit Logging ✓
- [ ] `core/services/audit_logger.py` - Audit logging service
- [ ] `lalo-frontend/src/components/admin/AuditLogs.tsx` - Log viewer UI
- [ ] Database migration for audit_logs table
- [ ] Tests in `tests/test_audit_logger.py`
- [ ] Integration in all critical operations (workflow, tools, auth)

### Step 19 - Data Governance ✓
- [ ] `core/models/governance_policy.py` - Data policy models
- [ ] `core/services/data_governor.py` - Governance service
- [ ] Database migration for governance tables
- [ ] Tests in `tests/test_data_governor.py`
- [ ] PII detection integrated in tool execution

### Step 20 - Secrets Management ✓
- [ ] `core/services/secrets_manager.py` - Enhanced secrets service
- [ ] Tests in `tests/test_secrets_manager.py`
- [ ] Updated `core/services/key_management.py` to use secrets_manager
- [ ] Secret rotation functionality working

---

## Final Verification Commands

Run these commands to verify everything works:

```bash
# 1. Verify you're on correct branch
git branch --show-current
# Expected: cf/phase3-frontend-ux

# 2. Verify tools still exist
ls core/tools/*.py | wc -l
# Expected: 10

# 3. Verify imports work
python -c "from core.services.rbac import rbac_service; from core.services.audit_logger import audit_logger; from core.services.data_governor import data_governor; from core.services.secrets_manager import secrets_manager; print('All imports successful')"

# 4. Run tests
python -m pytest tests/ -v

# 5. Check backend starts
python app.py
# Should start without errors
```

---

## Important Reminders

### What NOT to Do ❌
- ❌ DO NOT create new branches
- ❌ DO NOT checkout other branches
- ❌ DO NOT create new git remotes
- ❌ DO NOT modify existing tool files
- ❌ DO NOT delete any existing files
- ❌ DO NOT push to any remote except origin

### What TO Do ✅
- ✅ Stay on branch `cf/phase3-frontend-ux`
- ✅ Create only the files specified in Steps 17-20
- ✅ Follow existing code patterns and style
- ✅ Write comprehensive tests
- ✅ Run database migrations
- ✅ Verify all imports before committing
- ✅ Document any issues or blockers

---

## Success Criteria

When you're done, the system should have:
1. ✅ Complete RBAC with 3 roles and granular permissions
2. ✅ Comprehensive audit logging on all operations
3. ✅ Data governance with PII detection and masking
4. ✅ Enhanced secrets management with rotation
5. ✅ All tests passing
6. ✅ Database migrations applied
7. ✅ No broken imports or errors
8. ✅ Documentation updated

---

## Questions or Issues?

If you encounter any problems:
1. **DO NOT** try to fix by switching branches
2. **DO NOT** create workaround branches
3. **STOP** and document the issue
4. Report the specific error and wait for guidance

---

**BEGIN IMPLEMENTATION NOW**

Start with Step 20 (Secrets Management), then proceed to Steps 17, 18, and 19 in that order.

Good luck! 🚀
