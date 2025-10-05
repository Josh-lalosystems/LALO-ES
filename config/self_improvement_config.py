"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

# Self-improvement system configuration

# Sandbox Settings
SANDBOX_SETTINGS = {
    "max_concurrent_sandboxes": 3,
    "timeout_seconds": 3600,
    "max_memory_gb": 8,
    "enable_network": False,  # Sandbox network access
}

# Testing Framework
TESTING_SETTINGS = {
    "min_test_coverage": 0.90,
    "performance_threshold": 0.95,  # 95% of current performance
    "max_test_duration": 1800,  # 30 minutes
}

# Improvement Thresholds
IMPROVEMENT_THRESHOLDS = {
    "min_confidence_score": 0.95,
    "min_performance_gain": 0.10,  # 10% improvement
    "max_resource_increase": 0.15,  # 15% resource usage increase
}

# Safety Settings
SAFETY_SETTINGS = {
    "require_backup": True,
    "max_code_changes": 100,  # Max number of files to modify
    "protected_files": [
        "self_improvement_system.py",
        "security_manager.py",
        "backup_manager.py"
    ],
    "required_test_types": [
        "unit",
        "integration",
        "security",
        "performance"
    ]
}

# Improvement Types
ALLOWED_IMPROVEMENTS = {
    "connector": {
        "allowed_paths": ["connectors/", "tests/connectors/"],
        "required_tests": ["integration", "security"],
        "max_size_kb": 1000
    },
    "tool": {
        "allowed_paths": ["tools/", "tests/tools/"],
        "required_tests": ["unit", "integration"],
        "max_size_kb": 500
    },
    "agent": {
        "allowed_paths": ["agents/", "tests/agents/"],
        "required_tests": ["unit", "integration", "performance"],
        "max_size_kb": 2000
    },
    "model": {
        "allowed_paths": ["models/", "tests/models/"],
        "required_tests": ["performance", "reliability"],
        "max_size_kb": 5000
    }
}

# Learning Settings
LEARNING_SETTINGS = {
    "enable_self_training": True,
    "max_training_time": 7200,  # 2 hours
    "min_training_samples": 1000,
    "validation_split": 0.2
}
