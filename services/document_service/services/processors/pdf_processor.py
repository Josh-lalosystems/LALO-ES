"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from typing import Dict, Any
from io import BytesIO
import PyPDF2
from models import Document, ProcessingResult
from ..chunker import chunk_text_hierarchical

class PDFProcessor:
    async def process(self, document: Document) -> ProcessingResult:
        try:
            # Load PDF from bytes
            pdf = PyPDF2.PdfReader(BytesIO(document.content))
            
            # Extract metadata
            metadata: Dict[str, Any] = {
                "pages": len(pdf.pages),
                "is_encrypted": pdf.is_encrypted,
                "properties": {}
            }
            
            # Get document info
            if pdf.metadata:
                metadata["properties"] = {
                    "title": pdf.metadata.get('/Title', ''),
                    "author": pdf.metadata.get('/Author', ''),
                    "subject": pdf.metadata.get('/Subject', ''),
                    "keywords": pdf.metadata.get('/Keywords', ''),
                    "creator": pdf.metadata.get('/Creator', ''),
                    "producer": pdf.metadata.get('/Producer', '')
                }
            
            # Extract page information
            metadata["page_info"] = []
            page_texts = []
            for i, page in enumerate(pdf.pages):
                try:
                    page_info = {
                        "page_number": i + 1,
                        "size": page.mediabox.upper_right,
                        "rotation": page.get('/Rotate', 0),
                        "has_images": len(page.images) > 0
                    }
                    metadata["page_info"].append(page_info)
                    # Collect text for chunking (limit to first 50 pages to avoid huge memory)
                    if i < 50:
                        try:
                            page_texts.append(page.extract_text() or "")
                        except Exception:
                            page_texts.append("")
                except Exception:
                    # best-effort; continue
                    continue

            # Chunk the collected text
            try:
                full_text = "\n\n".join(page_texts)
                chunks = chunk_text_hierarchical(full_text, doc_id=document.id)
                document.metadata['chunks'] = chunks
            except Exception:
                document.metadata['chunks'] = []
            
            # Update document metadata
            document.metadata.update(metadata)
            
            return ProcessingResult(
                success=True,
                document_id=document.id,
                message="PDF document processed successfully"
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                document_id=document.id,
                errors=[f"PDF processing error: {str(e)}"]
            )
