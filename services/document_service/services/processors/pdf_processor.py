from typing import Dict, Any
from io import BytesIO
import PyPDF2
from models import Document, ProcessingResult

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
            for i, page in enumerate(pdf.pages):
                page_info = {
                    "page_number": i + 1,
                    "size": page.mediabox.upper_right,
                    "rotation": page.get('/Rotate', 0),
                    "has_images": len(page.images) > 0
                }
                metadata["page_info"].append(page_info)
            
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
