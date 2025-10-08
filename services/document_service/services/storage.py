"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from typing import Optional, List
import logging

try:
    from azure.storage.blob import BlobServiceClient
except Exception:
    BlobServiceClient = None  # type: ignore
import os
import json

from models import Document, StorageResult, UpdateResult

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = "documents"
        self.dead_letter_container = "dead_letters"

        if BlobServiceClient is None:
            logger.warning("Azure Storage client not available; document persistence disabled")
            self.blob_service_client = None
            return

        if not connection_string:
            logger.warning("AZURE_STORAGE_CONNECTION_STRING not set; document persistence disabled")
            self.blob_service_client = None
            return

        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        except Exception as exc:
            logger.warning("Failed to initialize Azure Storage client: %s", exc)
            self.blob_service_client = None

    def _storage_disabled(self) -> bool:
        if self.blob_service_client is None:
            logger.debug("Document storage is disabled")
            return True
        return False

    async def store_document(self, document: Document) -> StorageResult:
        if self._storage_disabled():
            return StorageResult(success=False, location="", errors=["Azure storage not configured"])

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

    async def store_dead_letter(self, job_id: str, job: dict) -> bool:
        """Persist a dead-letter job as JSON into the dead_letters container."""
        if self._storage_disabled():
            return False

        try:
            container_client = self.blob_service_client.get_container_client(self.dead_letter_container)
            try:
                container_client.create_container()
            except Exception:
                # container may already exist
                pass

            blob_name = f"{job_id}.json"
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(json.dumps(job), overwrite=True)
            return True
        except Exception:
            return False

    async def list_dead_letters(self) -> list:
        if self._storage_disabled():
            return []

        try:
            container_client = self.blob_service_client.get_container_client(self.dead_letter_container)
            blobs = container_client.list_blobs()
            results = []
            for b in blobs:
                blob_client = container_client.get_blob_client(b.name)
                content = blob_client.download_blob().readall()
                try:
                    results.append(json.loads(content))
                except Exception:
                    results.append({"name": b.name})
            return results
        except Exception:
            return []
    
    async def retrieve_document(self, doc_id: str) -> Optional[Document]:
        if self._storage_disabled():
            return None

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
