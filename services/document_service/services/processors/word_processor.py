from typing import Dict, Any
from io import BytesIO
from docx import Document as DocxDocument
from models import Document, ProcessingResult

class WordProcessor:
    async def process(self, document: Document) -> ProcessingResult:
        try:
            # Load document from bytes
            doc = DocxDocument(BytesIO(document.content))
            
            # Extract metadata
            metadata: Dict[str, Any] = {
                "paragraphs": len(doc.paragraphs),
                "sections": len(doc.sections),
                "tables": len(doc.tables),
                "styles": [],
                "properties": {}
            }
            
            # Get styles
            for style in doc.styles:
                if not style.name.startswith('@'):
                    metadata["styles"].append(style.name)
            
            # Get document properties
            if doc.core_properties:
                metadata["properties"] = {
                    "title": doc.core_properties.title,
                    "author": doc.core_properties.author,
                    "subject": doc.core_properties.subject,
                    "keywords": doc.core_properties.keywords,
                    "category": doc.core_properties.category,
                    "modified": doc.core_properties.modified.isoformat() if doc.core_properties.modified else None
                }
            
            # Update document metadata
            document.metadata.update(metadata)
            
            return ProcessingResult(
                success=True,
                document_id=document.id,
                message="Word document processed successfully"
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                document_id=document.id,
                errors=[f"Word processing error: {str(e)}"]
            )
