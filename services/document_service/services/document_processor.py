"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from typing import Optional, List
from ..models import Document, DocumentType, ProcessingResult
from .processors import (
    ExcelProcessor,
    WordProcessor,
    PDFProcessor,
    DefaultProcessor
)
from .quality import score_document
from .background_indexer import enqueue_index_job
import os
from core.vectorstores import get_vector_store

# INDEXING_MODE: 'sync' | 'background' | 'redis' (background uses in-memory queue if REDIS_URL not set)
INDEXING_MODE = os.getenv('INDEXING_MODE', 'background').lower()

class DocumentProcessor:
    def __init__(self):
        self.processors = {
            DocumentType.EXCEL: ExcelProcessor(),
            DocumentType.WORD: WordProcessor(),
            DocumentType.PDF: PDFProcessor(),
            DocumentType.OTHER: DefaultProcessor()
        }
        
    async def process_document(self, document: Document) -> ProcessingResult:
        try:
            # Detect file type. Try to use python-magic if available; otherwise
            # fall back to simple signature heuristics to avoid import-time
            # failures on systems without libmagic.
            mime_type = ""
            try:
                import magic
                m = magic.Magic(mime=True)
                mime_type = m.from_buffer(document.content)
            except Exception:
                # graceful fallback heuristics
                head = document.content[:16]
                if head.startswith(b"%PDF"):
                    mime_type = "application/pdf"
                elif head.startswith(b"PK"):
                    # docx/xlsx/pptx are ZIP based - let later checks classify
                    mime_type = "application/zip"
                else:
                    try:
                        # try UTF-8 text detect
                        _ = document.content.decode('utf-8')
                        mime_type = "text/plain"
                    except Exception:
                        mime_type = "application/octet-stream"
            
            # Update document type
            if "spreadsheet" in mime_type or "excel" in mime_type:
                document.type = DocumentType.EXCEL
            elif "word" in mime_type or "docx" in mime_type:
                document.type = DocumentType.WORD
            elif "pdf" in mime_type:
                document.type = DocumentType.PDF
            
            # Run lightweight quality scoring and attach to metadata
            try:
                qscore, qdetails = score_document(document.content, mime_type)
                document.metadata = document.metadata or {}
                document.metadata['quality'] = {
                    'score': qscore,
                    'details': qdetails
                }
            except Exception:
                # non-fatal; continue to processing
                pass

            # If document is very low quality, mark for manual review and skip heavy processing
            if document.metadata.get('quality', {}).get('details', {}).get('category') == 'garbage':
                return ProcessingResult(
                    success=False,
                    document_id=document.id,
                    errors=["Document requires manual review due to low quality"],
                )

            # Get appropriate processor
            processor = self.processors.get(document.type, self.processors[DocumentType.OTHER])

            # Process document
            result = await processor.process(document)

            # After processing, if chunks were produced, upsert them to vector store
            try:
                chunks = document.metadata.get('chunks', []) if document.metadata else []
                if chunks:
                    # Prepare lists for add_documents: texts, ids, metadatas
                    texts = [c.get('text', '') for c in chunks]
                    ids = [c.get('chunk_id') for c in chunks]
                    metadatas = [
                        {k: v for k, v in c.items() if k not in ('text',)} for c in chunks
                    ]

                    try:
                        if INDEXING_MODE == 'sync':
                            # perform synchronous upsert
                            store = get_vector_store()
                            await store.add_documents(documents=texts, ids=ids, metadatas=metadatas)
                        else:
                            enqueue_index_job(documents=texts, ids=ids, metadatas=metadatas)
                    except Exception:
                        # non-fatal
                        pass

            except Exception:
                # non-fatal
                pass

            return result
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                document_id=document.id,
                errors=[str(e)]
            )
