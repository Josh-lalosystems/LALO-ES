# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Module: SafetyValidationFramework

Purpose:
- Ensures safety of self-modifications
- Validates system integrity
- Prevents harmful changes
- Maintains operational boundaries
- Provides rollback capabilities
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import ast
import json
import logging
from pathlib import Path
import re

from .audit_logger import AuditLogger
from .sandbox_manager import SandboxManager
from .enhanced_memory_manager import EnhancedMemoryManager

class SafetyLevel(Enum):
    CRITICAL = "critical"  # Changes to core safety systems
    HIGH = "high"         # Changes to main functionality
    MEDIUM = "medium"     # Changes to auxiliary systems
    LOW = "low"          # Non-critical changes

class ValidationResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NEEDS_REVIEW = "needs_review"

@dataclass
class SafetyCheck:
    name: str
    description: str
    level: SafetyLevel
    validation_function: str
    parameters: Dict
    required: bool = True

@dataclass
class ValidationReport:
    timestamp: datetime
    checks_performed: List[Dict]
    result: ValidationResult
    issues: List[Dict]
    recommendations: List[str]
    metadata: Dict = field(default_factory=dict)

class SafetyValidator:
    """Core safety validation system"""
    
    def __init__(self):
        self.sandbox_manager = SandboxManager()
        self.memory_manager = EnhancedMemoryManager()
        self.audit = AuditLogger()
        self.load_safety_checks()
        
    def load_safety_checks(self):
        """Loads safety check definitions"""
        self.safety_checks = {
            "code": self._get_code_safety_checks(),
            "resource": self._get_resource_safety_checks(),
            "security": self._get_security_safety_checks(),
            "integrity": self._get_integrity_safety_checks(),
            "operational": self._get_operational_safety_checks()
        }
        
    async def validate_change(self, 
                            change_proposal: Dict,
                            safety_level: SafetyLevel) -> ValidationReport:
        """Validates a proposed change against safety checks"""
        checks_performed = []
        issues = []
        
        # Run relevant safety checks based on safety level
        for category, checks in self.safety_checks.items():
            for check in checks:
                if check.level.value <= safety_level.value:
                    result = await self._run_safety_check(check, change_proposal)
                    checks_performed.append({
                        "check": check.name,
                        "result": result["status"],
                        "details": result["details"]
                    })
                    
                    if result["status"] == ValidationResult.FAIL:
                        issues.append(result)
                        
        # Determine overall result
        overall_result = self._determine_overall_result(checks_performed, issues)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(issues)
        
        report = ValidationReport(
            timestamp=datetime.now(),
            checks_performed=checks_performed,
            result=overall_result,
            issues=issues,
            recommendations=recommendations,
            metadata={"safety_level": safety_level.value}
        )
        
        # Log validation report
        self.audit.log_validation_report(report)
        
        return report
        
    async def _run_safety_check(self, 
                               check: SafetyCheck,
                               proposal: Dict) -> Dict:
        """Executes a single safety check"""
        try:
            # Get the validation function
            validator = getattr(self, check.validation_function)
            
            # Run the check
            result = await validator(proposal, **check.parameters)
            
            return {
                "status": result["status"],
                "details": result["details"],
                "check": check.name
            }
            
        except Exception as e:
            logging.error(f"Error in safety check {check.name}: {str(e)}")
            return {
                "status": ValidationResult.FAIL,
                "details": f"Check failed with error: {str(e)}",
                "check": check.name
            }
            
    def _determine_overall_result(self,
                                checks: List[Dict],
                                issues: List[Dict]) -> ValidationResult:
        """Determines overall validation result"""
        if any(i["status"] == ValidationResult.FAIL for i in issues):
            return ValidationResult.FAIL
            
        if len(issues) > 0:
            return ValidationResult.WARNING
            
        if any(c["result"] == ValidationResult.NEEDS_REVIEW for c in checks):
            return ValidationResult.NEEDS_REVIEW
            
        return ValidationResult.PASS
        
    async def validate_code_safety(self, code_changes: Dict) -> Dict:
        """Validates code changes for safety"""
        results = {
            "syntax": await self._check_syntax(code_changes),
            "dangerous_patterns": await self._check_dangerous_patterns(code_changes),
            "resource_usage": await self._check_resource_usage(code_changes),
            "security": await self._check_security_implications(code_changes)
        }
        
        return results
        
    async def _check_syntax(self, code_changes: Dict) -> Dict:
        """Checks code syntax and structure"""
        issues = []
        for file_path, new_code in code_changes.items():
            try:
                ast.parse(new_code)
            except SyntaxError as e:
                issues.append({
                    "file": file_path,
                    "line": e.lineno,
                    "message": str(e)
                })
        
        return {
            "status": ValidationResult.FAIL if issues else ValidationResult.PASS,
            "issues": issues
        }
        
    async def _check_dangerous_patterns(self, code_changes: Dict) -> Dict:
        """Checks for dangerous code patterns"""
        dangerous_patterns = [
            (r"os\.system", "Direct system command execution"),
            (r"eval\(", "Code evaluation"),
            (r"exec\(", "Code execution"),
            (r"__import__", "Dynamic imports"),
            (r"subprocess\.", "Subprocess execution"),
            (r"open\(.+,'w'", "File writing"),
            (r"requests?\.delete", "HTTP DELETE requests")
        ]
        
        issues = []
        for file_path, new_code in code_changes.items():
            for pattern, description in dangerous_patterns:
                matches = re.finditer(pattern, new_code)
                for match in matches:
                    issues.append({
                        "file": file_path,
                        "pattern": pattern,
                        "description": description,
                        "line": new_code.count('\n', 0, match.start()) + 1
                    })
                    
        return {
            "status": ValidationResult.FAIL if issues else ValidationResult.PASS,
            "issues": issues
        }
        
    async def validate_resource_safety(self, 
                                     resource_requirements: Dict) -> Dict:
        """Validates resource usage safety"""
        results = {
            "memory": await self._check_memory_safety(resource_requirements),
            "cpu": await self._check_cpu_safety(resource_requirements),
            "disk": await self._check_disk_safety(resource_requirements),
            "network": await self._check_network_safety(resource_requirements)
        }
        
        return results
        
    async def validate_operational_safety(self, 
                                        operational_changes: Dict) -> Dict:
        """Validates operational safety aspects"""
        results = {
            "availability": await self._check_availability_impact(operational_changes),
            "performance": await self._check_performance_impact(operational_changes),
            "dependencies": await self._check_dependency_impact(operational_changes)
        }
        
        return results
        
    async def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """Generates recommendations for addressing issues"""
        recommendations = set()
        
        for issue in issues:
            if "pattern" in issue:
                recommendations.add(
                    f"Replace usage of {issue['pattern']} with a safer alternative"
                )
            if "resource" in issue:
                recommendations.add(
                    f"Optimize {issue['resource']} usage or increase limits"
                )
                
        return list(recommendations)
