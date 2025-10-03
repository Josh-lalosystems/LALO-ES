# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Module: SandboxManager

Purpose:
- Creates and manages isolated environments for testing self-improvements
- Handles resource allocation and cleanup
- Provides secure execution boundaries
- Manages state comparison and validation
"""

import docker
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib
from datetime import datetime
import resource
import psutil

from .audit_logger import AuditLogger
from .config.self_improvement_config import SANDBOX_SETTINGS

@dataclass
class SandboxMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_usage: float
    execution_time: float

@dataclass
class SandboxState:
    files_changed: List[str]
    modules_loaded: List[str]
    dependencies_added: List[str]
    environment_vars: Dict[str, str]
    resource_usage: SandboxMetrics

class ResourceMonitor:
    """Monitors and controls resource usage in sandbox environments"""
    
    def __init__(self, limits: Dict):
        self.limits = limits
        self.usage_history = []
        
    async def check_resources(self, sandbox_id: str) -> SandboxMetrics:
        """Monitors current resource usage"""
        process = psutil.Process()
        
        metrics = SandboxMetrics(
            cpu_usage=process.cpu_percent() / psutil.cpu_count(),
            memory_usage=process.memory_percent(),
            disk_usage=psutil.disk_usage('/').percent,
            network_usage=self._get_network_usage(),
            execution_time=process.cpu_times().user
        )
        
        self.usage_history.append({
            "timestamp": datetime.now().isoformat(),
            "sandbox_id": sandbox_id,
            "metrics": metrics
        })
        
        return metrics
        
    def _get_network_usage(self) -> float:
        """Calculates network usage"""
        net_io = psutil.net_io_counters()
        return (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024  # MB

    async def enforce_limits(self, metrics: SandboxMetrics) -> bool:
        """Ensures sandbox stays within resource limits"""
        if metrics.cpu_usage > self.limits["max_cpu_percent"]:
            return False
        if metrics.memory_usage > self.limits["max_memory_percent"]:
            return False
        if metrics.disk_usage > self.limits["max_disk_percent"]:
            return False
        return True

class StateManager:
    """Manages and compares sandbox states"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.state_history = {}
        
    async def capture_state(self, sandbox_id: str) -> SandboxState:
        """Captures current state of sandbox"""
        sandbox_path = self.base_path / sandbox_id
        
        state = SandboxState(
            files_changed=await self._get_changed_files(sandbox_path),
            modules_loaded=await self._get_loaded_modules(),
            dependencies_added=await self._get_dependencies(sandbox_path),
            environment_vars=dict(os.environ),
            resource_usage=await self._get_resource_usage()
        )
        
        self.state_history[sandbox_id] = state
        return state
        
    async def _get_changed_files(self, path: Path) -> List[str]:
        """Tracks changed files in sandbox"""
        changed_files = []
        for file in path.rglob("*"):
            if file.is_file():
                file_hash = self._calculate_file_hash(file)
                orig_file = Path.cwd() / file.relative_to(path)
                if orig_file.exists():
                    orig_hash = self._calculate_file_hash(orig_file)
                    if file_hash != orig_hash:
                        changed_files.append(str(file.relative_to(path)))
                else:
                    changed_files.append(str(file.relative_to(path)))
        return changed_files
        
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculates SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

class SandboxManager:
    """Main sandbox management class"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.base_path = Path("./sandboxes")
        self.active_sandboxes = {}
        self.resource_monitor = ResourceMonitor(SANDBOX_SETTINGS)
        self.state_manager = StateManager(self.base_path)
        self.audit = AuditLogger()
        
    async def create_sandbox(self, 
                           improvement_id: str,
                           code_changes: Dict[str, str]) -> str:
        """Creates new sandbox environment"""
        sandbox_id = f"sandbox_{improvement_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        sandbox_path = self.base_path / sandbox_id
        
        try:
            # Create sandbox directory
            sandbox_path.mkdir(parents=True)
            
            # Copy current codebase
            await self._copy_codebase(sandbox_path)
            
            # Apply code changes
            await self._apply_changes(sandbox_path, code_changes)
            
            # Create docker container
            container = await self._create_container(sandbox_id, sandbox_path)
            
            # Capture initial state
            initial_state = await self.state_manager.capture_state(sandbox_id)
            
            self.active_sandboxes[sandbox_id] = {
                "path": sandbox_path,
                "container": container,
                "initial_state": initial_state,
                "created_at": datetime.now()
            }
            
            self.audit.log_sandbox_creation(sandbox_id, initial_state)
            
            return sandbox_id
            
        except Exception as e:
            await self._cleanup_sandbox(sandbox_id)
            raise

    async def _copy_codebase(self, target_path: Path):
        """Copies current codebase to sandbox"""
        ignore_patterns = shutil.ignore_patterns(
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.git',
            '.env',
            'sandboxes',
            'backups'
        )
        shutil.copytree(Path.cwd(), target_path, ignore=ignore_patterns, dirs_exist_ok=True)

    async def _create_container(self, 
                              sandbox_id: str, 
                              sandbox_path: Path) -> docker.models.containers.Container:
        """Creates docker container for sandbox"""
        return self.docker_client.containers.run(
            "python:3.11-slim",
            name=f"lalo_sandbox_{sandbox_id}",
            command="tail -f /dev/null",  # Keep container running
            volumes={
                str(sandbox_path): {
                    'bind': '/app',
                    'mode': 'rw'
                }
            },
            environment={
                "PYTHONPATH": "/app",
                "SANDBOX_ID": sandbox_id,
                "SANDBOX_MODE": "true"
            },
            cpu_period=100000,  # CPU quota period in microseconds
            cpu_quota=int(100000 * SANDBOX_SETTINGS["max_cpu_cores"]),  # CPU quota in microseconds
            mem_limit=f"{SANDBOX_SETTINGS['max_memory_gb']}g",
            network_mode="none" if not SANDBOX_SETTINGS["enable_network"] else "bridge",
            detach=True,
            auto_remove=True
        )

    async def execute_in_sandbox(self, 
                               sandbox_id: str,
                               command: str) -> Tuple[int, str]:
        """Executes command in sandbox environment"""
        if sandbox_id not in self.active_sandboxes:
            raise ValueError(f"Sandbox {sandbox_id} not found")
            
        container = self.active_sandboxes[sandbox_id]["container"]
        
        # Check resource usage before execution
        metrics = await self.resource_monitor.check_resources(sandbox_id)
        if not await self.resource_monitor.enforce_limits(metrics):
            raise ResourceWarning("Sandbox resource limits exceeded")
            
        # Execute command
        exit_code, output = container.exec_run(
            f"cd /app && {command}",
            environment={"PYTHONPATH": "/app"}
        )
        
        # Log execution
        self.audit.log_sandbox_execution(
            sandbox_id,
            command,
            exit_code,
            metrics
        )
        
        return exit_code, output.decode()

    async def compare_states(self, 
                           sandbox_id: str,
                           include_resources: bool = True) -> Dict:
        """Compares current sandbox state with initial state"""
        if sandbox_id not in self.active_sandboxes:
            raise ValueError(f"Sandbox {sandbox_id} not found")
            
        initial_state = self.active_sandboxes[sandbox_id]["initial_state"]
        current_state = await self.state_manager.capture_state(sandbox_id)
        
        comparison = {
            "files_changed": list(set(current_state.files_changed) - 
                                set(initial_state.files_changed)),
            "modules_added": list(set(current_state.modules_loaded) - 
                                set(initial_state.modules_loaded)),
            "dependencies_added": list(set(current_state.dependencies_added) - 
                                    set(initial_state.dependencies_added)),
            "env_vars_changed": {}
        }
        
        # Compare environment variables
        for key, value in current_state.environment_vars.items():
            if key not in initial_state.environment_vars or \
               initial_state.environment_vars[key] != value:
                comparison["env_vars_changed"][key] = value
                
        if include_resources:
            comparison["resource_changes"] = {
                "cpu_delta": current_state.resource_usage.cpu_usage - 
                            initial_state.resource_usage.cpu_usage,
                "memory_delta": current_state.resource_usage.memory_usage - 
                               initial_state.resource_usage.memory_usage,
                "disk_delta": current_state.resource_usage.disk_usage - 
                             initial_state.resource_usage.disk_usage
            }
            
        return comparison

    async def destroy_sandbox(self, sandbox_id: str):
        """Cleans up sandbox environment"""
        if sandbox_id in self.active_sandboxes:
            await self._cleanup_sandbox(sandbox_id)
            self.audit.log_sandbox_destruction(sandbox_id)

    async def _cleanup_sandbox(self, sandbox_id: str):
        """Removes sandbox container and files"""
        if sandbox_id in self.active_sandboxes:
            try:
                # Stop and remove container
                self.active_sandboxes[sandbox_id]["container"].stop()
            except:
                pass
                
            try:
                # Remove sandbox directory
                shutil.rmtree(self.active_sandboxes[sandbox_id]["path"])
            except:
                pass
                
            del self.active_sandboxes[sandbox_id]
