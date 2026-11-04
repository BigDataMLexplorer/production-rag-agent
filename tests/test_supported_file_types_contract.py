SUPPORTED={".txt",".md",".pdf",".docx"}
def test_supported_document_types()->None:
    assert ".pdf" in SUPPORTED;assert ".docx" in SUPPORTED;assert ".exe" not in SUPPORTED
