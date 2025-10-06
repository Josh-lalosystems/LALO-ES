"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import magic
from ...models import Document, ProcessingResult

class DefaultProcessor:
    async def process(self, document: Document) -> ProcessingResult:
        try:
            # Use python-magic to get MIME type
            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(document.content)
            
            # Basic metadata
            metadata = {
                "mime_type": mime_type,
                "size_bytes": len(document.content),
                "properties": {}
            }
            
            # Update document metadata
            document.metadata.update(metadata)
            
            return ProcessingResult(
                success=True,
                document_id=document.id,
                message="Document processed with default processor"
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                document_id=document.id,
                errors=[f"Default processing error: {str(e)}"]
            )
