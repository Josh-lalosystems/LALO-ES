import sys
sys.path.append(r"c:\IT\LALOai-main")
from services.document_service.services.quality import score_document
from services.document_service.services.chunker import chunk_text_hierarchical


def test_quality_and_chunking():
    content = (b"This is a high quality document. " * 100)
    score, details = score_document(content, mime_type='text/plain')
    assert score >= 30
    # chunk the decoded text
    text = content.decode('utf-8')
    chunks = chunk_text_hierarchical(text, doc_id='t1')
    assert len(chunks) > 0
