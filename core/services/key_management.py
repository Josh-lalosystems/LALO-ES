from typing import Optional, Dict
from pydantic import BaseModel, SecretStr
from fastapi import HTTPException, status
from sqlalchemy import Column, String, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import os
from cryptography.fernet import Fernet
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

# Initialize encryption
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY") or Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

# Database setup - use shared database
from ..database import Base, SessionLocal, engine, APIKeys

class APIKeyRequest(BaseModel):
    openai_key: Optional[SecretStr]
    anthropic_key: Optional[SecretStr]
    # Add other API keys as needed

class KeyManager:
    def get_session(self):
        """Get a database session"""
        return SessionLocal()
    
    def get_keys(self, user_id: str) -> Dict[str, str]:
        """Get API keys for a user"""
        with self.get_session() as db:
            record = db.query(APIKeys).filter(APIKeys.user_id == user_id).first()
            if not record:
                return {}
            return record.keys
    
    def set_keys(self, user_id: str, keys: APIKeyRequest):
        """Store or update API keys for a user"""
        with self.get_session() as db:
            record = db.query(APIKeys).filter(APIKeys.user_id == user_id).first()
            if not record:
                record = APIKeys(user_id=user_id)
                db.add(record)
            
            # Update existing keys dictionary
            current_keys = record.keys
            if keys.openai_key:
                current_keys["openai"] = keys.openai_key.get_secret_value()
            if keys.anthropic_key:
                current_keys["anthropic"] = keys.anthropic_key.get_secret_value()
            
            record.keys = current_keys
            db.commit()
    
    def delete_keys(self, user_id: str):
        """Delete all API keys for a user"""
        with self.get_session() as db:
            record = db.query(APIKeys).filter(APIKeys.user_id == user_id).first()
            if record:
                db.delete(record)
                db.commit()
    
    async def validate_keys(self, user_id: str) -> Dict[str, bool]:
        """Validate that stored API keys are working"""
        keys = self.get_keys(user_id)
        status = {}
        
        if "openai" in keys:
            # Test OpenAI key
            try:
                client = AsyncOpenAI(api_key=keys["openai"])
                await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                status["openai"] = True
            except:
                status["openai"] = False
        
        if "anthropic" in keys:
            # Test Anthropic key
            try:
                client = AsyncAnthropic(api_key=keys["anthropic"])
                await client.messages.create(
                    model="claude-instant-1",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                status["anthropic"] = True
            except:
                status["anthropic"] = False
        
        return status

# Global instance
key_manager = KeyManager()
