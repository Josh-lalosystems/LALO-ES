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

"""
Code Execution Tool

Safely executes code in isolated Docker containers:
- Python code execution
- JavaScript/Node.js execution
- Resource limits (CPU, memory, time)
- Network disabled for security
- Automatic cleanup
"""

import os
import asyncio
import tempfile
import hashlib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

from .base import BaseTool, ToolDefinition, ToolParameter, ToolExecutionResult


class CodeExecutorTool(BaseTool):
    """Secure code execution tool using Docker containers"""

    def __init__(self):
        self._docker_available = False
        self._check_docker_availability()

        # Resource limits
        self._timeout_seconds = int(os.getenv("CODE_EXEC_TIMEOUT", "30"))
        self._memory_limit = os.getenv("CODE_EXEC_MEMORY_LIMIT", "256m")
        self._cpu_quota = int(os.getenv("CODE_EXEC_CPU_QUOTA", "50000"))  # 50% of 1 CPU

        # Image names
        self._python_image = os.getenv("PYTHON_DOCKER_IMAGE", "python:3.11-slim")
        self._node_image = os.getenv("NODE_DOCKER_IMAGE", "node:18-slim")

    def _check_docker_availability(self):
        """Check if Docker is available"""
        try:
            import docker
            client = docker.from_env()
            client.ping()
            self._docker_available = True
        except Exception:
            self._docker_available = False

    @property
    def tool_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="code_executor",
            description="Execute code safely in an isolated Docker container. Supports Python and JavaScript/Node.js. Network access is disabled for security.",
            parameters=[
                ToolParameter(
                    name="code",
                    type="string",
                    description="The code to execute",
                    required=True
                ),
                ToolParameter(
                    name="language",
                    type="string",
                    description="Programming language: 'python' or 'javascript'",
                    required=True,
                    enum=["python", "javascript", "js", "node"]
                ),
                ToolParameter(
                    name="timeout",
                    type="integer",
                    description="Maximum execution time in seconds (default: 30, max: 300)",
                    required=False
                ),
                ToolParameter(
                    name="dependencies",
                    type="array",
                    description="List of package dependencies to install (e.g., ['requests', 'numpy'] for Python or ['axios'] for Node.js)",
                    required=False
                ),
                ToolParameter(
                    name="stdin",
                    type="string",
                    description="Standard input to provide to the program",
                    required=False
                )
            ],
            returns={
                "type": "object",
                "description": "Execution result with stdout, stderr, exit code, and execution time"
            }
        )

    async def execute(self, **kwargs) -> ToolExecutionResult:
        """Execute code in Docker container"""
        if not self._docker_available:
            return ToolExecutionResult(
                success=False,
                error="Docker is not available. Please install Docker and ensure it's running."
            )

        code = kwargs.get("code")
        language = kwargs.get("language", "python").lower()
        timeout = min(kwargs.get("timeout", self._timeout_seconds), 300)  # Max 5 minutes
        dependencies = kwargs.get("dependencies", [])
        stdin = kwargs.get("stdin", "")

        # Normalize language
        if language in ["js", "node", "javascript"]:
            language = "javascript"
        elif language not in ["python", "javascript"]:
            return ToolExecutionResult(
                success=False,
                error=f"Unsupported language: {language}. Use 'python' or 'javascript'."
            )

        try:
            if language == "python":
                result = await self._execute_python(code, timeout, dependencies, stdin)
            else:  # javascript
                result = await self._execute_javascript(code, timeout, dependencies, stdin)

            return ToolExecutionResult(
                success=result["exit_code"] == 0,
                output=result,
                metadata={
                    "language": language,
                    "timeout": timeout,
                    "dependencies": dependencies
                }
            )

        except asyncio.TimeoutError:
            return ToolExecutionResult(
                success=False,
                error=f"Execution timed out after {timeout} seconds",
                output={
                    "stdout": "",
                    "stderr": f"Timeout: execution exceeded {timeout} seconds",
                    "exit_code": -1,
                    "execution_time": timeout
                }
            )
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f"Execution failed: {str(e)}",
                output={
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1,
                    "execution_time": 0
                }
            )

    async def _execute_python(
        self,
        code: str,
        timeout: int,
        dependencies: list,
        stdin: str
    ) -> Dict:
        """Execute Python code in Docker container"""
        import docker

        client = docker.from_env()

        # Create temporary directory for code
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write code to file
            code_file = tmpdir_path / "script.py"
            code_file.write_text(code)

            # Create requirements file if dependencies provided
            if dependencies:
                requirements = tmpdir_path / "requirements.txt"
                requirements.write_text("\n".join(dependencies))

            # Build command
            if dependencies:
                command = f"pip install -q -r /workspace/requirements.txt && python /workspace/script.py"
            else:
                command = "python /workspace/script.py"

            # Run container
            start_time = datetime.utcnow()
            try:
                container = client.containers.run(
                    image=self._python_image,
                    command=["sh", "-c", command],
                    volumes={str(tmpdir_path): {'bind': '/workspace', 'mode': 'ro'}},
                    working_dir='/workspace',
                    network_disabled=True,  # Disable network for security
                    mem_limit=self._memory_limit,
                    cpu_quota=self._cpu_quota,
                    detach=True,
                    stdin_open=bool(stdin),
                    remove=True
                )

                # Provide stdin if needed
                if stdin:
                    container.attach_socket(stdin=True)

                # Wait for container with timeout
                result = container.wait(timeout=timeout)
                execution_time = (datetime.utcnow() - start_time).total_seconds()

                # Get logs
                stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
                stderr = container.logs(stdout=False, stderr=True).decode('utf-8')

                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": result["StatusCode"],
                    "execution_time": execution_time,
                    "language": "python",
                    "timestamp": datetime.utcnow().isoformat()
                }

            except docker.errors.ContainerError as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                return {
                    "stdout": e.stdout.decode('utf-8') if e.stdout else "",
                    "stderr": e.stderr.decode('utf-8') if e.stderr else str(e),
                    "exit_code": e.exit_status,
                    "execution_time": execution_time,
                    "language": "python",
                    "timestamp": datetime.utcnow().isoformat()
                }

    async def _execute_javascript(
        self,
        code: str,
        timeout: int,
        dependencies: list,
        stdin: str
    ) -> Dict:
        """Execute JavaScript code in Docker container"""
        import docker

        client = docker.from_env()

        # Create temporary directory for code
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write code to file
            code_file = tmpdir_path / "script.js"
            code_file.write_text(code)

            # Create package.json if dependencies provided
            if dependencies:
                package_json = {
                    "name": "code-execution",
                    "version": "1.0.0",
                    "dependencies": {pkg: "latest" for pkg in dependencies}
                }
                import json
                (tmpdir_path / "package.json").write_text(json.dumps(package_json))

            # Build command
            if dependencies:
                command = f"npm install --silent && node /workspace/script.js"
            else:
                command = "node /workspace/script.js"

            # Run container
            start_time = datetime.utcnow()
            try:
                container = client.containers.run(
                    image=self._node_image,
                    command=["sh", "-c", command],
                    volumes={str(tmpdir_path): {'bind': '/workspace', 'mode': 'ro'}},
                    working_dir='/workspace',
                    network_disabled=True,  # Disable network for security
                    mem_limit=self._memory_limit,
                    cpu_quota=self._cpu_quota,
                    detach=True,
                    stdin_open=bool(stdin),
                    remove=True
                )

                # Provide stdin if needed
                if stdin:
                    container.attach_socket(stdin=True)

                # Wait for container with timeout
                result = container.wait(timeout=timeout)
                execution_time = (datetime.utcnow() - start_time).total_seconds()

                # Get logs
                stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
                stderr = container.logs(stdout=False, stderr=True).decode('utf-8')

                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": result["StatusCode"],
                    "execution_time": execution_time,
                    "language": "javascript",
                    "timestamp": datetime.utcnow().isoformat()
                }

            except docker.errors.ContainerError as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                return {
                    "stdout": e.stdout.decode('utf-8') if e.stdout else "",
                    "stderr": e.stderr.decode('utf-8') if e.stderr else str(e),
                    "exit_code": e.exit_status,
                    "execution_time": execution_time,
                    "language": "javascript",
                    "timestamp": datetime.utcnow().isoformat()
                }

    def is_enabled(self) -> bool:
        """Tool is enabled if Docker is available"""
        return self._docker_available


# Create singleton instance
code_executor_tool = CodeExecutorTool()
