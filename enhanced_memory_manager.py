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
Module: EnhancedMemoryManager

Purpose:
- Implements dual-layer memory architecture (session + permanent)
- Manages temporary workspace for active sessions
- Handles permanent storage of valuable training data
- Provides semantic search capabilities
- Maintains comprehensive audit trail

Architecture:
- Session Memory: Fast, temporary storage for active workflows
- Permanent Memory: Long-term storage with semantic search
- Training Data: Curated experiences for system improvement
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
import json
import chromadb
from chromadb.config import Settings
from audit_logger import AuditLogger

class SessionMemory:
    def __init__(self):
        self.active_sessions = {}
        self.session_metadata = {}
        
    def create_session(self, session_id: str = None) -> str:
        """Creates a new session workspace"""
        session_id = session_id or str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "workflow_steps": [],
            "feedback_history": [],
            "state_backups": [],
            "confidence_scores": [],
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        }
        return session_id
    
    def add_workflow_step(self, session_id: str, step_data: Dict):
        """Records a workflow step in session memory"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["workflow_steps"].append(step_data)
            self.active_sessions[session_id]["last_updated"] = datetime.utcnow()
    
    def add_feedback(self, session_id: str, feedback_data: Dict):
        """Records user feedback in session memory"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["feedback_history"].append(feedback_data)
            self.active_sessions[session_id]["last_updated"] = datetime.utcnow()

class PermanentMemory:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=persist_directory
        ))
        self.collections = {
            "workflows": self.chroma_client.get_or_create_collection("workflows"),
            "feedback": self.chroma_client.get_or_create_collection("feedback"),
            "training_data": self.chroma_client.get_or_create_collection("training_data")
        }
        
    def store_workflow(self, session_data: Dict):
        """Stores completed workflow in permanent memory"""
        workflow_id = str(uuid.uuid4())
        
        # Extract metadata and embed content
        metadata = {
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence_scores": json.dumps(session_data.get("confidence_scores", [])),
            "success_rate": self._calculate_success_rate(session_data)
        }
        
        # Store in ChromaDB
        self.collections["workflows"].add(
            ids=[workflow_id],
            documents=[json.dumps(session_data)],
            metadatas=[metadata]
        )
        
    def store_training_data(self, data: Dict):
        """Stores curated training data for system improvement"""
        data_id = str(uuid.uuid4())
        
        metadata = {
            "data_id": data_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data_type": data.get("type", "general"),
            "quality_score": data.get("quality_score", 0.0)
        }
        
        self.collections["training_data"].add(
            ids=[data_id],
            documents=[json.dumps(data)],
            metadatas=[metadata]
        )

    def _calculate_success_rate(self, session_data: Dict) -> float:
        """Calculates success rate based on feedback"""
        feedback = session_data.get("feedback_history", [])
        if not feedback:
            return 0.0
            
        positive_feedback = sum(1 for f in feedback if f.get("rating", 0) > 0.7)
        return positive_feedback / len(feedback)

class EnhancedMemoryManager:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.session_memory = SessionMemory()
        self.permanent_memory = PermanentMemory(persist_directory)
        self.audit = AuditLogger()
        
    def start_session(self) -> str:
        """Starts a new workflow session"""
        return self.session_memory.create_session()
        
    def record_step(self, session_id: str, step_data: Dict):
        """Records a workflow step"""
        self.session_memory.add_workflow_step(session_id, step_data)
        self.audit.log_workflow_step(session_id, step_data)
        
    def record_feedback(self, session_id: str, feedback_data: Dict):
        """Records user feedback"""
        self.session_memory.add_feedback(session_id, feedback_data)
        self.audit.log_feedback(session_id, feedback_data)
        
    def commit_session(self, session_id: str):
        """Commits session to permanent memory"""
        if session_id in self.session_memory.active_sessions:
            session_data = self.session_memory.active_sessions[session_id]
            
            # Store in permanent memory
            self.permanent_memory.store_workflow(session_data)
            
            # If session was high quality, store as training data
            if self._is_valuable_training_data(session_data):
                self.permanent_memory.store_training_data({
                    "type": "workflow",
                    "data": session_data,
                    "quality_score": self._calculate_training_value(session_data)
                })
                
            # Cleanup session
            del self.session_memory.active_sessions[session_id]
            
    def _is_valuable_training_data(self, session_data: Dict) -> bool:
        """Determines if session should be used for training"""
        success_rate = self.permanent_memory._calculate_success_rate(session_data)
        feedback_quality = self._calculate_feedback_quality(session_data)
        return success_rate > 0.8 and feedback_quality > 0.7
        
    def _calculate_training_value(self, session_data: Dict) -> float:
        """Calculates the training value of a session"""
        success_rate = self.permanent_memory._calculate_success_rate(session_data)
        feedback_quality = self._calculate_feedback_quality(session_data)
        workflow_complexity = len(session_data.get("workflow_steps", []))
        
        # Weighted scoring
        return (
            success_rate * 0.4 +
            feedback_quality * 0.4 +
            min(1.0, workflow_complexity / 10) * 0.2
        )
        
    def _calculate_feedback_quality(self, session_data: Dict) -> float:
        """Calculates the quality of feedback in a session"""
        feedback = session_data.get("feedback_history", [])
        if not feedback:
            return 0.0
            
        # Consider feedback detail and consistency
        detailed_feedback = sum(1 for f in feedback if len(f.get("comment", "")) > 50)
        return detailed_feedback / len(feedback)
