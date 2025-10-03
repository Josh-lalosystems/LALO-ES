# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Module: AdminCenter

Purpose:
- Provides administrative interface for LALO configuration
- Manages knowledge sources and seed data
- Monitors self-improvement and analysis
- Controls model usage and connectors
- Configures safety parameters
"""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional, Union
from datetime import datetime
import jwt
from pathlib import Path

from .safety_validation_framework import SafetyValidator, SafetyLevel
from .self_analysis_system import SelfAnalysisSystem
from .enhanced_memory_manager import EnhancedMemoryManager
from .audit_logger import AuditLogger

class KnowledgeSource(BaseModel):
    url: HttpUrl
    category: str
    description: str
    trust_level: float
    metadata: Dict = {}

class Connector(BaseModel):
    name: str
    type: str
    config: Dict
    description: str
    enabled: bool = True

class ModelConfig(BaseModel):
    model_id: str
    provider: str
    purpose: str
    max_tokens: int
    temperature: float
    enabled: bool = True
    cost_per_token: float
    monthly_budget: float

class SeedData(BaseModel):
    category: str
    content: Union[str, Dict]
    description: str
    priority: int

class AdminCenter:
    """Main administrative interface"""
    
    def __init__(self):
        self.safety_validator = SafetyValidator()
        self.analysis_system = SelfAnalysisSystem()
        self.memory_manager = EnhancedMemoryManager()
        self.audit = AuditLogger()
        
    async def add_knowledge_source(self, source: KnowledgeSource) -> Dict:
        """Adds new knowledge source"""
        # Validate source
        validation = await self.safety_validator.validate_change(
            {"type": "knowledge_source", "data": source.dict()},
            SafetyLevel.MEDIUM
        )
        
        if validation.result.value in ["fail", "needs_review"]:
            raise ValueError(f"Source validation failed: {validation.issues}")
            
        # Add to knowledge base
        await self.analysis_system.knowledge_manager.verify_and_cache_source(
            str(source.url),
            source.category
        )
        
        # Log addition
        self.audit.log_admin_action(
            "add_knowledge_source",
            {"source": source.dict()}
        )
        
        return {"status": "success", "source_id": source.url}
        
    async def add_connector(self, connector: Connector) -> Dict:
        """Adds new connector configuration"""
        # Validate connector
        validation = await self.safety_validator.validate_change(
            {"type": "connector", "data": connector.dict()},
            SafetyLevel.HIGH
        )
        
        if validation.result.value in ["fail", "needs_review"]:
            raise ValueError(f"Connector validation failed: {validation.issues}")
            
        # Store connector configuration
        await self.memory_manager.store_connector_config(connector.dict())
        
        # Log addition
        self.audit.log_admin_action(
            "add_connector",
            {"connector": connector.dict()}
        )
        
        return {"status": "success", "connector_id": connector.name}
        
    async def configure_model(self, config: ModelConfig) -> Dict:
        """Configures model usage parameters"""
        # Validate configuration
        validation = await self.safety_validator.validate_change(
            {"type": "model_config", "data": config.dict()},
            SafetyLevel.HIGH
        )
        
        if validation.result.value in ["fail", "needs_review"]:
            raise ValueError(f"Model configuration validation failed: {validation.issues}")
            
        # Store model configuration
        await self.memory_manager.store_model_config(config.dict())
        
        # Log configuration
        self.audit.log_admin_action(
            "configure_model",
            {"config": config.dict()}
        )
        
        return {"status": "success", "model_id": config.model_id}
        
    async def add_seed_data(self, data: SeedData) -> Dict:
        """Adds seed data for system training"""
        # Validate data
        validation = await self.safety_validator.validate_change(
            {"type": "seed_data", "data": data.dict()},
            SafetyLevel.MEDIUM
        )
        
        if validation.result.value in ["fail", "needs_review"]:
            raise ValueError(f"Seed data validation failed: {validation.issues}")
            
        # Store seed data
        await self.memory_manager.store_seed_data(data.dict())
        
        # Log addition
        self.audit.log_admin_action(
            "add_seed_data",
            {"data": data.dict()}
        )
        
        return {"status": "success", "data_id": f"{data.category}_{datetime.now().timestamp()}"}
        
    async def get_system_status(self) -> Dict:
        """Gets current system status"""
        analysis_report = await self.analysis_system.get_analysis_report()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis_report,
            "active_models": await self._get_active_models(),
            "active_connectors": await self._get_active_connectors(),
            "knowledge_sources": await self._get_knowledge_sources(),
            "system_health": await self._get_system_health()
        }
        
    async def get_improvement_history(self) -> List[Dict]:
        """Gets history of system improvements"""
        return await self.memory_manager.get_improvement_history()
        
    async def get_analysis_history(self) -> List[Dict]:
        """Gets history of system analysis reports"""
        return await self.memory_manager.get_analysis_history()
        
    async def _get_system_health(self) -> Dict:
        """Gets system health metrics"""
        return {
            "memory_usage": await self._get_memory_usage(),
            "model_usage": await self._get_model_usage(),
            "error_rates": await self._get_error_rates(),
            "performance_metrics": await self._get_performance_metrics()
        }

# FastAPI Router for Admin API
router = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
admin_center = AdminCenter()

@router.post("/knowledge-sources")
async def add_knowledge_source(
    source: KnowledgeSource,
    token: str = Depends(oauth2_scheme)
):
    return await admin_center.add_knowledge_source(source)

@router.post("/connectors")
async def add_connector(
    connector: Connector,
    token: str = Depends(oauth2_scheme)
):
    return await admin_center.add_connector(connector)

@router.post("/models")
async def configure_model(
    config: ModelConfig,
    token: str = Depends(oauth2_scheme)
):
    return await admin_center.configure_model(config)

@router.post("/seed-data")
async def add_seed_data(
    data: SeedData,
    token: str = Depends(oauth2_scheme)
):
    return await admin_center.add_seed_data(data)

@router.get("/status")
async def get_system_status(
    token: str = Depends(oauth2_scheme)
):
    return await admin_center.get_system_status()

@router.get("/improvements")
async def get_improvement_history(
    token: str = Depends(oauth2_scheme)
):
    return await admin_center.get_improvement_history()

@router.get("/analysis")
async def get_analysis_history(
    token: str = Depends(oauth2_scheme)
):
    return await admin_center.get_analysis_history()
