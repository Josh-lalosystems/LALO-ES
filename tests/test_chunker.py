from services.document_service.services.chunker import chunk_text_hierarchical


def test_chunker_paragraph_and_sentence():
    text = "This is first paragraph. It has two sentences.\n\nSecond paragraph here! Short." 
    chunks = chunk_text_hierarchical(text, doc_id="doc1")
    # Expect at least 3 chunks: paragraph1, sentences, paragraph2
    assert any(c['level'] == 'paragraph' for c in chunks)
    assert any(c['level'] == 'sentence' for c in chunks)
    # Check chunk ids include doc id
    assert all("doc1" in c['chunk_id'] for c in chunks)
