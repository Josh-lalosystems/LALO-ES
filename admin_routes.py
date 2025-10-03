# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional

from .admin_center_extended import (
    AdminCenterExtended,
    StorageConfig,
    Pipeline,
    LLMConfig,
    Prompt,
    IndexConfig,
    MemoryConfig,
    IngestionConfig,
    GovernanceRule,
    SecurityPolicy,
    Webhook,
    OperationalMetrics,
    ObservabilityConfig,
    AnalyticsConfig,
    AuditConfig
)

router = APIRouter(prefix="/admin", tags=["admin"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
admin = AdminCenterExtended()

# Storage Management
@router.post("/storage")
async def configure_storage(
    config: StorageConfig,
    token: str = Depends(oauth2_scheme)
):
    """Configure storage settings"""
    return await admin.configure_storage(config)

@router.get("/storage")
async def get_storage_config(
    token: str = Depends(oauth2_scheme)
):
    """Get current storage configuration"""
    return {"config": await admin._get_storage_config()}

# Pipeline Management
@router.post("/pipelines")
async def create_pipeline(
    pipeline: Pipeline,
    token: str = Depends(oauth2_scheme)
):
    """Create new pipeline"""
    return await admin.manage_pipeline(pipeline)

@router.get("/pipelines")
async def list_pipelines(
    token: str = Depends(oauth2_scheme)
):
    """List all pipelines"""
    return {"pipelines": await admin._list_pipelines()}

# LLM Management
@router.post("/llm")
async def configure_llm(
    config: LLMConfig,
    token: str = Depends(oauth2_scheme)
):
    """Configure LLM settings"""
    return await admin.configure_llm(config)

@router.get("/llm")
async def get_llm_config(
    token: str = Depends(oauth2_scheme)
):
    """Get current LLM configuration"""
    return {"config": await admin._get_llm_config()}

# Prompt Management
@router.post("/prompts")
async def create_prompt(
    prompt: Prompt,
    token: str = Depends(oauth2_scheme)
):
    """Create new prompt template"""
    return await admin.manage_prompt(prompt)

@router.get("/prompts")
async def list_prompts(
    token: str = Depends(oauth2_scheme)
):
    """List all prompt templates"""
    return {"prompts": await admin._list_prompts()}

# Index Management
@router.post("/indexes")
async def configure_index(
    config: IndexConfig,
    token: str = Depends(oauth2_scheme)
):
    """Configure vector index"""
    return await admin.configure_index(config)

@router.get("/indexes")
async def list_indexes(
    token: str = Depends(oauth2_scheme)
):
    """List all indexes"""
    return {"indexes": await admin._list_indexes()}

# Memory Management
@router.post("/memory")
async def configure_memory(
    config: MemoryConfig,
    token: str = Depends(oauth2_scheme)
):
    """Configure memory settings"""
    return await admin.configure_memory(config)

# Ingestion Management
@router.post("/ingestion")
async def configure_ingestion(
    config: IngestionConfig,
    token: str = Depends(oauth2_scheme)
):
    """Configure ingestion settings"""
    return await admin.configure_ingestion(config)

# Governance Management
@router.post("/governance")
async def add_governance_rule(
    rule: GovernanceRule,
    token: str = Depends(oauth2_scheme)
):
    """Add governance rule"""
    return await admin.add_governance_rule(rule)

@router.get("/governance")
async def list_governance_rules(
    token: str = Depends(oauth2_scheme)
):
    """List all governance rules"""
    return {"rules": await admin._list_governance_rules()}

# Security Management
@router.post("/security")
async def configure_security(
    policy: SecurityPolicy,
    token: str = Depends(oauth2_scheme)
):
    """Configure security policy"""
    return await admin.configure_security(policy)

# Webhook Management
@router.post("/webhooks")
async def create_webhook(
    webhook: Webhook,
    token: str = Depends(oauth2_scheme)
):
    """Create new webhook"""
    return await admin.manage_webhook(webhook)

@router.get("/webhooks")
async def list_webhooks(
    token: str = Depends(oauth2_scheme)
):
    """List all webhooks"""
    return {"webhooks": await admin._list_webhooks()}

# Operations Management
@router.post("/operations")
async def configure_operations(
    metrics: OperationalMetrics,
    token: str = Depends(oauth2_scheme)
):
    """Configure operational metrics"""
    return await admin.configure_operations(metrics)

# Observability Management
@router.post("/observability")
async def configure_observability(
    config: ObservabilityConfig,
    token: str = Depends(oauth2_scheme)
):
    """Configure observability settings"""
    return await admin.configure_observability(config)

# Analytics Management
@router.post("/analytics")
async def configure_analytics(
    config: AnalyticsConfig,
    token: str = Depends(oauth2_scheme)
):
    """Configure analytics settings"""
    return await admin.configure_analytics(config)

# Audit Management
@router.post("/audit")
async def configure_audit(
    config: AuditConfig,
    token: str = Depends(oauth2_scheme)
):
    """Configure audit settings"""
    return await admin.configure_audit(config)

@router.get("/overview")
async def get_system_overview(
    token: str = Depends(oauth2_scheme)
):
    """Get system overview"""
    return {
        "storage": await admin._get_storage_stats(),
        "pipelines": await admin._get_pipeline_stats(),
        "llm": await admin._get_llm_stats(),
        "memory": await admin._get_memory_stats(),
        "ingestion": await admin._get_ingestion_stats(),
        "security": await admin._get_security_stats(),
        "operations": await admin._get_operational_stats()
    }
