from typing import Optional, List
import magic
from models import Document, DocumentType, ProcessingResult
from .processors import (
    ExcelProcessor,
    WordProcessor,
    PDFProcessor,
    DefaultProcessor
)

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
            # Detect file type
            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(document.content)
            
            # Update document type
            if "spreadsheet" in mime_type or "excel" in mime_type:
                document.type = DocumentType.EXCEL
            elif "word" in mime_type or "docx" in mime_type:
                document.type = DocumentType.WORD
            elif "pdf" in mime_type:
                document.type = DocumentType.PDF
            
            # Get appropriate processor
            processor = self.processors.get(document.type, self.processors[DocumentType.OTHER])
            
            # Process document
            return await processor.process(document)
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                document_id=document.id,
                errors=[str(e)]
            )
