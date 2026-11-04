from pathlib import Path
from docx import Document as DocxDocument
from pypdf import PdfReader
def parse_file(path:Path)->list[tuple[int|None,str]]:
    suffix=path.suffix.lower()
    if suffix in {".txt",".md"}:return [(None,path.read_text(encoding="utf-8"))]
    if suffix==".pdf":
        reader=PdfReader(str(path));return [(i+1,page.extract_text() or "") for i,page in enumerate(reader.pages)]
    if suffix==".docx":
        doc=DocxDocument(str(path));return [(None,"\n".join(p.text for p in doc.paragraphs))]
    raise ValueError(f"Unsupported file type: {suffix}")
