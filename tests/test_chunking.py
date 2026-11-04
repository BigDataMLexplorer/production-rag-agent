from app.ingestion.chunking import chunk_text
def test_chunking_keeps_overlap_and_content()->None:
    chunks=chunk_text("word "*1000,max_chars=300,overlap=50);assert len(chunks)>1;assert all(c.content for c in chunks)
