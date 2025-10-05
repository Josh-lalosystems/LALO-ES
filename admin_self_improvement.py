"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

from pydantic import BaseModel
from typing import Dict, List, Optional, Union
from enum import Enum
from datetime import datetime

class ModelType(Enum):
    LLM = "llm"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    SEMANTIC_SEARCH = "semantic_search"
    CONFIDENCE_SCORING = "confidence_scoring"
    PLANNING = "planning"
    REASONING = "reasoning"
    SPECIALIZED = "specialized"

class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CUSTOM = "custom"

class ImprovementCategory(Enum):
    CORE = "core"
    CONNECTOR = "connector"
    MODEL = "model"
    PERFORMANCE = "performance"
    CAPABILITY = "capability"
    SECURITY = "security"

class ModelConfig(BaseModel):
    name: str
    type: ModelType
    provider: ModelProvider
    version: str
    purpose: str
    capabilities: List[str]
    parameters: Dict
    resource_requirements: Dict
    performance_metrics: Dict
    cost_config: Optional[Dict]
    fallback_model: Optional[str]
    enabled: bool = True

class SelfImprovementConfig(BaseModel):
    enabled: bool = True
    improvement_categories: List[ImprovementCategory]
    sandbox_settings: Dict
    validation_thresholds: Dict
    approval_required: bool = True
    max_concurrent_improvements: int
    improvement_schedule: Dict
    rollback_settings: Dict

class ImprovementMetrics(BaseModel):
    category: ImprovementCategory
    success_rate: float
    impact_score: float
    resource_usage: Dict
    rollback_rate: float
    average_validation_score: float
    user_feedback_score: Optional[float]

class AdminSelfImprovement:
    """Administrative interface for self-improvement systems"""

    async def get_improvement_dashboard(self) -> Dict:
        """Get overview of self-improvement system status"""
        return {
            "active_improvements": await self._get_active_improvements(),
            "pending_approvals": await self._get_pending_approvals(),
            "recent_changes": await self._get_recent_changes(),
            "system_health": await self._get_system_health(),
            "performance_metrics": await self._get_performance_metrics(),
            "resource_usage": await self._get_resource_usage()
        }

    async def configure_self_improvement(self, config: SelfImprovementConfig) -> Dict:
        """Configure self-improvement system settings"""
        validation = await self._validate_improvement_config(config)
        if validation.get("valid"):
            await self._apply_improvement_config(config)
            return {"status": "success", "config": config.dict()}
        return {"status": "error", "issues": validation.get("issues", [])}

    async def review_improvement_proposal(self, proposal_id: str, action: str) -> Dict:
        """Review and approve/reject improvement proposals"""
        proposal = await self._get_improvement_proposal(proposal_id)
        if action == "approve":
            return await self._approve_improvement(proposal)
        elif action == "reject":
            return await self._reject_improvement(proposal)
        raise ValueError("Invalid action")

    async def get_improvement_history(self, 
                                    category: Optional[ImprovementCategory] = None,
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> List[Dict]:
        """Get history of system improvements"""
        filters = {
            "category": category,
            "start_date": start_date,
            "end_date": end_date
        }
        return await self._query_improvement_history(filters)

    async def get_model_registry(self) -> Dict:
        """Get overview of all registered models"""
        return {
            "active_models": await self._get_active_models(),
            "model_performance": await self._get_model_performance(),
            "resource_usage": await self._get_model_resource_usage(),
            "cost_analysis": await self._get_model_cost_analysis()
        }

    async def register_model(self, config: ModelConfig) -> Dict:
        """Register a new model in the system"""
        validation = await self._validate_model_config(config)
        if validation.get("valid"):
            await self._register_new_model(config)
            return {"status": "success", "model_id": config.name}
        return {"status": "error", "issues": validation.get("issues", [])}

    async def update_model_config(self, model_name: str, config: ModelConfig) -> Dict:
        """Update existing model configuration"""
        validation = await self._validate_model_config(config)
        if validation.get("valid"):
            await self._update_model(model_name, config)
            return {"status": "success", "model": config.dict()}
        return {"status": "error", "issues": validation.get("issues", [])}

    async def get_model_metrics(self, model_name: str) -> Dict:
        """Get detailed metrics for specific model"""
        return {
            "performance": await self._get_detailed_performance(model_name),
            "usage": await self._get_usage_statistics(model_name),
            "costs": await self._get_cost_metrics(model_name),
            "errors": await self._get_error_statistics(model_name)
        }

    async def configure_fallback_chain(self, 
                                     model_name: str, 
                                     fallback_chain: List[str]) -> Dict:
        """Configure model fallback sequence"""
        validation = await self._validate_fallback_chain(model_name, fallback_chain)
        if validation.get("valid"):
            await self._set_fallback_chain(model_name, fallback_chain)
            return {"status": "success", "fallback_chain": fallback_chain}
        return {"status": "error", "issues": validation.get("issues", [])}

    async def get_improvement_metrics(self, 
                                    category: Optional[ImprovementCategory] = None) -> List[ImprovementMetrics]:
        """Get metrics for self-improvement system"""
        return await self._calculate_improvement_metrics(category)

    async def configure_sandbox(self, settings: Dict) -> Dict:
        """Configure sandbox environment settings"""
        validation = await self._validate_sandbox_settings(settings)
        if validation.get("valid"):
            await self._apply_sandbox_settings(settings)
            return {"status": "success", "settings": settings}
        return {"status": "error", "issues": validation.get("issues", [])}
