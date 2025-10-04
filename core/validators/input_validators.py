# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Input Validation and Sanitization Functions
"""

import re
import html
import os
from typing import Any, Dict
from pathlib import Path


def sanitize_sql(value: str) -> str:
    """
    Sanitize SQL input to prevent SQL injection

    Note: This is a secondary defense. Always use parameterized queries.
    """
    if not isinstance(value, str):
        return str(value)

    # Remove dangerous SQL keywords and characters
    dangerous_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bOR\b.*=.*)",
        r"('.*--)",
    ]

    sanitized = value
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

    # Escape single quotes
    sanitized = sanitized.replace("'", "''")

    return sanitized.strip()


def sanitize_xss(value: str) -> str:
    """
    Sanitize input to prevent XSS attacks
    """
    if not isinstance(value, str):
        return str(value)

    # HTML escape
    sanitized = html.escape(value)

    # Remove dangerous HTML tags and attributes
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'javascript:',
        r'on\w+\s*=',  # onclick, onload, etc.
        r'<embed[^>]*>',
        r'<object[^>]*>',
    ]

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)

    return sanitized


def sanitize_command(value: str) -> str:
    """
    Sanitize input to prevent command injection
    """
    if not isinstance(value, str):
        return str(value)

    # Remove shell metacharacters
    dangerous_chars = ['|', '&', ';', '$', '`', '\n', '(', ')', '<', '>', '\\']
    sanitized = value

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')

    # Remove command substitution
    sanitized = re.sub(r'\$\(.*?\)', '', sanitized)
    sanitized = re.sub(r'`.*?`', '', sanitized)

    return sanitized.strip()


def sanitize_path(value: str, allowed_root: str = None) -> str:
    """
    Sanitize file path to prevent path traversal

    Args:
        value: Path to sanitize
        allowed_root: Optional root directory to enforce

    Raises:
        ValueError: If path attempts traversal outside allowed root
    """
    if not isinstance(value, str):
        value = str(value)

    # Remove null bytes
    sanitized = value.replace('\x00', '')

    # Normalize path
    normalized = os.path.normpath(sanitized)

    # Check for path traversal attempts
    if '..' in normalized:
        raise ValueError("Path traversal detected")

    # If allowed_root specified, ensure path is within it
    if allowed_root:
        allowed_root = os.path.abspath(allowed_root)
        full_path = os.path.abspath(os.path.join(allowed_root, normalized))

        if not full_path.startswith(allowed_root):
            raise ValueError(f"Path outside allowed root: {allowed_root}")

        return full_path

    return normalized


def validate_workflow_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize workflow request
    """
    validated = {}

    # User request (text)
    if 'user_request' in data:
        validated['user_request'] = sanitize_xss(str(data['user_request']))

        # Check length
        if len(validated['user_request']) > 10000:
            raise ValueError("Request too long (max 10000 characters)")

    # Prebuilt workflow ID
    if 'prebuilt_workflow_id' in data:
        workflow_id = str(data['prebuilt_workflow_id'])
        # Only alphanumeric and hyphens
        if not re.match(r'^[a-zA-Z0-9\-]+$', workflow_id):
            raise ValueError("Invalid workflow ID format")
        validated['prebuilt_workflow_id'] = workflow_id

    return validated


def validate_tool_input(tool_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize tool-specific input
    """
    validated = {}

    # Common validations
    for key, value in data.items():
        if isinstance(value, str):
            # Sanitize strings
            if key in ['query', 'prompt', 'text', 'content']:
                validated[key] = sanitize_xss(value)
            elif key in ['path', 'file_path', 'directory']:
                validated[key] = sanitize_path(value)
            elif key in ['sql', 'query_string']:
                validated[key] = sanitize_sql(value)
            elif key in ['command', 'shell_cmd']:
                validated[key] = sanitize_command(value)
            else:
                validated[key] = sanitize_xss(value)
        else:
            validated[key] = value

    # Tool-specific validations
    if tool_name == 'web_search':
        if 'query' in validated and len(validated['query']) > 500:
            raise ValueError("Search query too long (max 500 characters)")

    elif tool_name == 'code_executor':
        if 'code' in validated and len(validated['code']) > 50000:
            raise ValueError("Code too long (max 50KB)")

        # Check for dangerous patterns in code
        if 'code' in validated:
            dangerous_imports = ['os.system', 'subprocess.call', 'eval(', 'exec(']
            for pattern in dangerous_imports:
                if pattern in validated['code']:
                    raise ValueError(f"Dangerous code pattern detected: {pattern}")

    elif tool_name == 'database_query':
        # Ensure only SELECT queries
        if 'sql' in validated:
            sql = validated['sql'].strip().upper()
            if not sql.startswith('SELECT') and not sql.startswith('WITH'):
                raise ValueError("Only SELECT queries allowed")

    return validated


def validate_agent_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize agent configuration
    """
    validated = {}

    # Agent name
    if 'name' in data:
        name = str(data['name'])
        if not re.match(r'^[a-zA-Z0-9\-_ ]+$', name):
            raise ValueError("Agent name can only contain alphanumeric, hyphens, underscores, and spaces")
        if len(name) > 100:
            raise ValueError("Agent name too long (max 100 characters)")
        validated['name'] = sanitize_xss(name)

    # System prompt
    if 'system_prompt' in data:
        prompt = str(data['system_prompt'])
        if len(prompt) > 5000:
            raise ValueError("System prompt too long (max 5000 characters)")
        validated['system_prompt'] = sanitize_xss(prompt)

    # Model name
    if 'model' in data:
        model = str(data['model'])
        allowed_models = [
            'gpt-4-turbo-preview', 'gpt-3.5-turbo',
            'claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'
        ]
        if model not in allowed_models:
            raise ValueError(f"Invalid model. Allowed: {', '.join(allowed_models)}")
        validated['model'] = model

    # Temperature
    if 'temperature' in data:
        temp = float(data['temperature'])
        if not 0.0 <= temp <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        validated['temperature'] = temp

    # Max tokens
    if 'max_tokens' in data:
        max_tokens = int(data['max_tokens'])
        if not 1 <= max_tokens <= 100000:
            raise ValueError("Max tokens must be between 1 and 100000")
        validated['max_tokens'] = max_tokens

    # Allowed tools (list)
    if 'allowed_tools' in data:
        if not isinstance(data['allowed_tools'], list):
            raise ValueError("Allowed tools must be a list")
        validated['allowed_tools'] = [sanitize_xss(str(tool)) for tool in data['allowed_tools']]

    return validated


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_api_key(key: str, provider: str) -> bool:
    """
    Validate API key format
    """
    if not isinstance(key, str) or not key:
        return False

    # OpenAI keys start with 'sk-'
    if provider == 'openai':
        return key.startswith('sk-') and len(key) > 20

    # Anthropic keys start with 'sk-ant-'
    elif provider == 'anthropic':
        return key.startswith('sk-ant-') and len(key) > 20

    # Other providers - basic length check
    return len(key) >= 10
