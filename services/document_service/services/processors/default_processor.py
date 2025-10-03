import magic
from models import Document, ProcessingResult

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
