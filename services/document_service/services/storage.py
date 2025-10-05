"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from typing import Optional, List
from azure.storage.blob import BlobServiceClient
from models import Document, StorageResult, UpdateResult
import os
import json

class StorageService:
    def __init__(self):
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = "documents"
        
    async def store_document(self, document: Document) -> StorageResult:
        try:
            # Get container client
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Store document content
            content_blob_name = f"{document.id}/content"
            content_blob = container_client.get_blob_client(content_blob_name)
            content_blob.upload_blob(document.content, overwrite=True)
            
            # Store metadata separately
            metadata_blob_name = f"{document.id}/metadata.json"
            metadata_blob = container_client.get_blob_client(metadata_blob_name)
            metadata_json = json.dumps({
                "name": document.name,
                "type": document.type,
                "metadata": document.metadata,
                "version": document.version,
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat(),
                "owner": document.owner,
                "permissions": [p.dict() for p in document.permissions]
            })
            metadata_blob.upload_blob(metadata_json, overwrite=True)
            
            return StorageResult(
                success=True,
                location=f"azure://{self.container_name}/{document.id}",
                errors=None
            )
            
        except Exception as e:
            return StorageResult(
                success=False,
                location="",
                errors=[str(e)]
            )
    
    async def retrieve_document(self, doc_id: str) -> Optional[Document]:
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Get metadata
            metadata_blob_name = f"{doc_id}/metadata.json"
            metadata_blob = container_client.get_blob_client(metadata_blob_name)
            metadata_content = metadata_blob.download_blob().readall()
            metadata = json.loads(metadata_content)
            
            # Get content
            content_blob_name = f"{doc_id}/content"
            content_blob = container_client.get_blob_client(content_blob_name)
            content = content_blob.download_blob().readall()
            
            # Reconstruct document
            return Document(
                id=doc_id,
                content=content,
                **metadata
            )
            
        except Exception:
            return None
    
    async def update_document(self, doc_id: str, updates: dict) -> UpdateResult:
        try:
            # Get existing document
            document = await self.retrieve_document(doc_id)
            if not document:
                return UpdateResult(
                    success=False,
                    document=None,
                    errors=["Document not found"]
                )
            
            # Update fields
            for key, value in updates.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            
            # Store updated document
            result = await self.store_document(document)
            if not result.success:
                return UpdateResult(
                    success=False,
                    document=None,
                    errors=result.errors
                )
            
            return UpdateResult(
                success=True,
                document=document,
                errors=None
            )
            
        except Exception as e:
            return UpdateResult(
                success=False,
                document=None,
                errors=[str(e)]
            )
