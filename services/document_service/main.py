from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import logging
from datetime import datetime
import uuid

from models import (
    Document,
    DocumentType,
    ProcessingResult,
    StorageResult,
    UpdateResult
)
from services.document_processor import DocumentProcessor
from services.storage import StorageService
from services.auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LALO Document Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_processor = DocumentProcessor()
storage_service = StorageService()

@app.post("/documents/upload", response_model=ProcessingResult)
async def upload_document(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
) -> ProcessingResult:
    try:
        # Read file content
        content = await file.read()
        
        # Create document
        doc = Document(
            id=str(uuid.uuid4()),
            name=file.filename,
            type=DocumentType.OTHER,  # Will be updated during processing
            content=content,
            metadata={},
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            owner=current_user,
            permissions=[]
        )
        
        # Process document
        result = await document_processor.process_document(doc)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.errors)
            
        # Store document
        storage_result = await storage_service.store_document(doc)
        if not storage_result.success:
            raise HTTPException(status_code=500, detail=storage_result.errors)
            
        return ProcessingResult(
            success=True,
            document_id=doc.id,
            message="Document processed and stored successfully"
        )
            
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}", response_model=Document)
async def get_document(
    doc_id: str,
    current_user: str = Depends(get_current_user)
) -> Document:
    try:
        doc = await storage_service.retrieve_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Check permissions
        if doc.owner != current_user and not any(
            p.user_id == current_user for p in doc.permissions
        ):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this document"
            )
            
        return doc
            
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/documents/{doc_id}", response_model=UpdateResult)
async def update_document(
    doc_id: str,
    updates: dict,
    current_user: str = Depends(get_current_user)
) -> UpdateResult:
    try:
        # Get existing document
        doc = await storage_service.retrieve_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Check permissions
        if doc.owner != current_user and not any(
            p.user_id == current_user and p.access_level == "write"
            for p in doc.permissions
        ):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to modify this document"
            )
            
        # Update document
        result = await storage_service.update_document(doc_id, updates)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.errors)
            
        return result
            
    except Exception as e:
        logger.error(f"Error updating document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8200)
