from typing import Optional, Dict
from pydantic import BaseModel, SecretStr
from fastapi import HTTPException, status
from sqlalchemy import Column, String, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import os
from cryptography.fernet import Fernet
try:
    from openai import AsyncOpenAI
except Exception:
    AsyncOpenAI = None  # type: ignore
try:
    from anthropic import AsyncAnthropic
except Exception:
    AsyncAnthropic = None  # type: ignore

# Initialize encryption
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY") or Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

# Database setup - use shared database
from ..database import Base, SessionLocal, engine, APIKeys

class APIKeyRequest(BaseModel):
    openai_key: Optional[SecretStr] = None
    anthropic_key: Optional[SecretStr] = None
    google_key: Optional[SecretStr] = None
    azure_key: Optional[SecretStr] = None
    huggingface_key: Optional[SecretStr] = None
    cohere_key: Optional[SecretStr] = None
    custom_key: Optional[SecretStr] = None
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
            if keys.google_key:
                current_keys["google"] = keys.google_key.get_secret_value()
            if keys.azure_key:
                current_keys["azure"] = keys.azure_key.get_secret_value()
            if keys.huggingface_key:
                current_keys["huggingface"] = keys.huggingface_key.get_secret_value()
            if keys.cohere_key:
                current_keys["cohere"] = keys.cohere_key.get_secret_value()
            if keys.custom_key:
                current_keys["custom"] = keys.custom_key.get_secret_value()
            
            record.keys = current_keys
            db.commit()
    
    def delete_keys(self, user_id: str):
        """Delete all API keys for a user"""
        with self.get_session() as db:
            record = db.query(APIKeys).filter(APIKeys.user_id == user_id).first()
            if record:
                db.delete(record)
                db.commit()

    def delete_key(self, user_id: str, provider: str):
        """Delete a specific provider key for a user"""
        provider = provider.lower()
        with self.get_session() as db:
            record = db.query(APIKeys).filter(APIKeys.user_id == user_id).first()
            if record:
                data = record.keys
                if provider in data:
                    del data[provider]
                    record.keys = data
                    db.commit()
                else:
                    # Nothing to delete; no-op
                    pass
    
    async def validate_keys(self, user_id: str) -> Dict[str, bool]:
        """Validate that stored API keys are working"""
        keys = self.get_keys(user_id)
        status: Dict[str, bool] = {}

        if "openai" in keys and AsyncOpenAI is not None:
            try:
                client = AsyncOpenAI(api_key=keys["openai"])
                # Make a minimal test call with minimal cost
                await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1  # Minimal cost - just 1 token
                )
                status["openai"] = True
            except Exception as e:
                print(f"OpenAI key validation failed: {str(e)}")
                status["openai"] = False

        if "anthropic" in keys and AsyncAnthropic is not None:
            try:
                client = AsyncAnthropic(api_key=keys["anthropic"])
                # Use Haiku for testing - fastest and cheapest
                await client.messages.create(
                    model="claude-3-haiku-20240307",
                    messages=[{"role": "user", "content": "test"}],
                    max_output_tokens=1  # Minimal cost - just 1 token
                )
                status["anthropic"] = True
            except Exception as e:
                print(f"Anthropic key validation failed: {str(e)}")
                status["anthropic"] = False

        return status

# Global instance
key_manager = KeyManager()
