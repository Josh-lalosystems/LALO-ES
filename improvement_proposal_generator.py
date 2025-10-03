# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Module: ImprovementProposalGenerator

Purpose:
- Analyzes system performance and patterns
- Generates improvement proposals
- Evaluates potential impacts
- Incorporates meta-learning for optimization
- Implements hierarchical planning for complex improvements
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import ast
import inspect
import json
from concurrent.futures import ThreadPoolExecutor

from .audit_logger import AuditLogger
from .enhanced_memory_manager import EnhancedMemoryManager
from .config.self_improvement_config import IMPROVEMENT_THRESHOLDS, ALLOWED_IMPROVEMENTS

class ImprovementCategory(Enum):
    PERFORMANCE = "performance"
    FUNCTIONALITY = "functionality"
    RELIABILITY = "reliability"
    SECURITY = "security"
    EFFICIENCY = "efficiency"
    CAPABILITY = "capability"

class ImprovementPriority(Enum):
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    EXPERIMENTAL = 1

@dataclass
class CodeChange:
    file_path: str
    original_code: str
    new_code: str
    change_type: str
    impact_analysis: Dict
    safety_score: float

@dataclass
class ImprovementProposal:
    id: str
    category: ImprovementCategory
    priority: ImprovementPriority
    description: str
    rationale: str
    code_changes: List[CodeChange]
    estimated_impact: Dict
    required_resources: Dict
    test_cases: List[Dict]
    safety_checks: List[str]
    rollback_plan: Dict
    metadata: Dict = field(default_factory=dict)

class PatternRecognizer:
    """Identifies patterns in system behavior and code"""
    
    def __init__(self, memory_manager: EnhancedMemoryManager):
        self.memory_manager = memory_manager
        self.pattern_cache = {}
        
    async def analyze_performance_patterns(self, metrics: List[Dict]) -> List[Dict]:
        """Identifies performance-related patterns"""
        patterns = []
        
        # Analyze response time patterns
        response_patterns = await self._analyze_metric_patterns(
            metrics, "response_time", threshold=1.0
        )
        patterns.extend(response_patterns)
        
        # Analyze resource usage patterns
        resource_patterns = await self._analyze_resource_patterns(metrics)
        patterns.extend(resource_patterns)
        
        # Analyze error patterns
        error_patterns = await self._analyze_error_patterns(metrics)
        patterns.extend(error_patterns)
        
        return patterns
        
    async def analyze_code_patterns(self, codebase_stats: Dict) -> List[Dict]:
        """Identifies patterns in code structure and usage"""
        patterns = []
        
        # Analyze code complexity patterns
        complexity_patterns = await self._analyze_complexity_patterns(codebase_stats)
        patterns.extend(complexity_patterns)
        
        # Analyze dependency patterns
        dependency_patterns = await self._analyze_dependency_patterns(codebase_stats)
        patterns.extend(dependency_patterns)
        
        return patterns

class ImpactAnalyzer:
    """Analyzes potential impacts of proposed changes"""
    
    def __init__(self):
        self.impact_history = {}
        
    async def analyze_impact(self, 
                           proposal: ImprovementProposal) -> Dict:
        """Analyzes potential impacts of a proposal"""
        impacts = {
            "performance": await self._analyze_performance_impact(proposal),
            "resources": await self._analyze_resource_impact(proposal),
            "dependencies": await self._analyze_dependency_impact(proposal),
            "security": await self._analyze_security_impact(proposal),
            "maintainability": await self._analyze_maintainability_impact(proposal)
        }
        
        # Calculate aggregate impact score
        impact_score = self._calculate_impact_score(impacts)
        impacts["overall_score"] = impact_score
        
        return impacts
        
    async def _analyze_performance_impact(self, proposal: ImprovementProposal) -> Dict:
        """Analyzes potential performance impacts"""
        perf_impact = {
            "response_time": 0.0,
            "throughput": 0.0,
            "resource_usage": 0.0
        }
        
        for change in proposal.code_changes:
            # Analyze code changes for performance implications
            if "async" in change.new_code and "async" not in change.original_code:
                perf_impact["response_time"] -= 0.1  # Potential improvement
                
            if "cache" in change.new_code and "cache" not in change.original_code:
                perf_impact["response_time"] -= 0.15
                
        return perf_impact

class SafetyValidator:
    """Validates safety aspects of proposed improvements"""
    
    def __init__(self):
        self.safety_checks = []
        
    async def validate_proposal(self, 
                              proposal: ImprovementProposal) -> Tuple[bool, List[str]]:
        """Validates safety of a proposal"""
        issues = []
        
        # Check code safety
        code_issues = await self._validate_code_safety(proposal.code_changes)
        issues.extend(code_issues)
        
        # Check resource safety
        resource_issues = await self._validate_resource_safety(proposal.required_resources)
        issues.extend(resource_issues)
        
        # Check security implications
        security_issues = await self._validate_security(proposal)
        issues.extend(security_issues)
        
        return len(issues) == 0, issues

class MetaLearningOptimizer:
    """Optimizes improvement generation through meta-learning"""
    
    def __init__(self, memory_manager: EnhancedMemoryManager):
        self.memory_manager = memory_manager
        self.learning_patterns = {}
        
    async def optimize_proposal(self, 
                              proposal: ImprovementProposal,
                              historical_data: Dict) -> ImprovementProposal:
        """Optimizes proposal based on learned patterns"""
        # Analyze historical success patterns
        success_patterns = await self._analyze_success_patterns(historical_data)
        
        # Apply learned optimizations
        optimized_proposal = await self._apply_optimizations(proposal, success_patterns)
        
        return optimized_proposal
        
    async def _analyze_success_patterns(self, historical_data: Dict) -> Dict:
        """Analyzes patterns in successful improvements"""
        success_patterns = {}
        
        for improvement in historical_data.get("successful_improvements", []):
            category = improvement["category"]
            if category not in success_patterns:
                success_patterns[category] = {
                    "common_changes": set(),
                    "success_rate": 0.0,
                    "avg_impact": 0.0
                }
            
            # Analyze common elements in successful improvements
            changes = set(c["change_type"] for c in improvement["code_changes"])
            success_patterns[category]["common_changes"].update(changes)
            
        return success_patterns

class ImprovementProposalGenerator:
    """Main class for generating improvement proposals"""
    
    def __init__(self):
        self.memory_manager = EnhancedMemoryManager()
        self.pattern_recognizer = PatternRecognizer(self.memory_manager)
        self.impact_analyzer = ImpactAnalyzer()
        self.safety_validator = SafetyValidator()
        self.meta_learner = MetaLearningOptimizer(self.memory_manager)
        self.audit = AuditLogger()
        
    async def generate_proposal(self, 
                              system_metrics: Dict,
                              improvement_type: str) -> Optional[ImprovementProposal]:
        """Generates an improvement proposal based on system metrics"""
        try:
            # Analyze patterns
            performance_patterns = await self.pattern_recognizer.analyze_performance_patterns(
                system_metrics.get("performance_history", [])
            )
            
            code_patterns = await self.pattern_recognizer.analyze_code_patterns(
                system_metrics.get("codebase_stats", {})
            )
            
            # Identify improvement opportunities
            opportunities = await self._identify_opportunities(
                performance_patterns,
                code_patterns,
                improvement_type
            )
            
            if not opportunities:
                return None
                
            # Generate proposal
            proposal = await self._create_proposal(opportunities[0], improvement_type)
            
            # Analyze impact
            impact = await self.impact_analyzer.analyze_impact(proposal)
            proposal.estimated_impact = impact
            
            # Validate safety
            is_safe, safety_issues = await self.safety_validator.validate_proposal(proposal)
            if not is_safe:
                self.audit.log_safety_issues(proposal.id, safety_issues)
                return None
                
            # Optimize through meta-learning
            historical_data = await self.memory_manager.get_improvement_history()
            optimized_proposal = await self.meta_learner.optimize_proposal(
                proposal,
                historical_data
            )
            
            return optimized_proposal
            
        except Exception as e:
            self.audit.log_error("proposal_generation", str(e))
            raise
            
    async def _identify_opportunities(self,
                                    performance_patterns: List[Dict],
                                    code_patterns: List[Dict],
                                    improvement_type: str) -> List[Dict]:
        """Identifies improvement opportunities"""
        opportunities = []
        
        # Check performance-based opportunities
        for pattern in performance_patterns:
            if pattern["impact"] >= IMPROVEMENT_THRESHOLDS["min_performance_gain"]:
                opportunities.append({
                    "type": "performance",
                    "pattern": pattern,
                    "priority": self._calculate_priority(pattern)
                })
                
        # Check code-based opportunities
        for pattern in code_patterns:
            if pattern.get("improvement_potential", 0) >= IMPROVEMENT_THRESHOLDS["min_code_improvement"]:
                opportunities.append({
                    "type": "code",
                    "pattern": pattern,
                    "priority": self._calculate_priority(pattern)
                })
                
        # Sort by priority
        opportunities.sort(key=lambda x: x["priority"].value, reverse=True)
        
        return opportunities
        
    async def _create_proposal(self,
                             opportunity: Dict,
                             improvement_type: str) -> ImprovementProposal:
        """Creates an improvement proposal"""
        proposal_id = f"imp_{improvement_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        code_changes = await self._generate_code_changes(opportunity)
        test_cases = await self._generate_test_cases(code_changes)
        
        proposal = ImprovementProposal(
            id=proposal_id,
            category=ImprovementCategory(opportunity["type"]),
            priority=opportunity["priority"],
            description=self._generate_description(opportunity),
            rationale=self._generate_rationale(opportunity),
            code_changes=code_changes,
            estimated_impact={},  # To be filled by impact analyzer
            required_resources=self._estimate_required_resources(code_changes),
            test_cases=test_cases,
            safety_checks=self._generate_safety_checks(code_changes),
            rollback_plan=self._generate_rollback_plan(code_changes),
            metadata={
                "generated_at": datetime.now().isoformat(),
                "opportunity_data": opportunity
            }
        )
        
        return proposal
        
    def _calculate_priority(self, pattern: Dict) -> ImprovementPriority:
        """Calculates priority of an improvement opportunity"""
        if pattern.get("impact", 0) > 0.8:
            return ImprovementPriority.CRITICAL
        elif pattern.get("impact", 0) > 0.6:
            return ImprovementPriority.HIGH
        elif pattern.get("impact", 0) > 0.4:
            return ImprovementPriority.MEDIUM
        elif pattern.get("impact", 0) > 0.2:
            return ImprovementPriority.LOW
        return ImprovementPriority.EXPERIMENTAL
        
    async def _generate_code_changes(self, opportunity: Dict) -> List[CodeChange]:
        """Generates specific code changes for an improvement"""
        changes = []
        
        if opportunity["type"] == "performance":
            changes.extend(await self._generate_performance_improvements(opportunity))
        elif opportunity["type"] == "code":
            changes.extend(await self._generate_code_improvements(opportunity))
            
        return changes
        
    async def _generate_test_cases(self, code_changes: List[CodeChange]) -> List[Dict]:
        """Generates test cases for proposed changes"""
        test_cases = []
        
        for change in code_changes:
            # Generate unit tests
            test_cases.extend(await self._generate_unit_tests(change))
            
            # Generate integration tests if needed
            if self._requires_integration_tests(change):
                test_cases.extend(await self._generate_integration_tests(change))
                
        return test_cases
        
    def _generate_safety_checks(self, code_changes: List[CodeChange]) -> List[str]:
        """Generates safety checks for code changes"""
        checks = []
        
        for change in code_changes:
            # Add basic safety checks
            checks.extend([
                f"Validate no critical path breaks in {change.file_path}",
                f"Verify resource usage within limits for {change.file_path}",
                f"Check for security vulnerabilities in {change.file_path}"
            ])
            
            # Add change-specific checks
            if "async" in change.new_code:
                checks.append(f"Verify async implementation in {change.file_path}")
                
        return checks
