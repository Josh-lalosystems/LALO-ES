"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class DocumentType(str, Enum):
    EXCEL = "excel"
    WORD = "word"
    PDF = "pdf"
    OTHER = "other"

class AccessLevel(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class Permission(BaseModel):
    user_id: str
    access_level: AccessLevel
    granted_at: datetime
    granted_by: str

class Document(BaseModel):
    id: str
    name: str
    type: DocumentType
    content: bytes
    metadata: Dict
    version: int
    created_at: datetime
    updated_at: datetime
    owner: str
    permissions: List[Permission]

class ProcessingResult(BaseModel):
    success: bool
    document_id: str
    message: Optional[str]
    errors: Optional[List[str]]

class StorageResult(BaseModel):
    success: bool
    location: str
    errors: Optional[List[str]]

class UpdateResult(BaseModel):
    success: bool
    document: Document
    errors: Optional[List[str]]
