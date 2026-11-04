from __future__ import annotations
from datetime import datetime
from pathlib import Path
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models import Chunk,Document,DocumentVersion
from app.ingestion.chunking import chunk_text
from app.ingestion.parsers import parse_file
from app.retrieval.embeddings import embed_texts
class DuplicateVersionError(ValueError):pass
def ingest_file(db:Session,*,tenant_id:UUID,external_id:str,title:str,version:str,path:Path,is_current:bool,effective_at:datetime|None,source_path:str|None=None)->DocumentVersion:
    document=db.query(Document).filter(Document.tenant_id==tenant_id,Document.external_id==external_id).one_or_none()
    if document is None: document=Document(tenant_id=tenant_id,external_id=external_id,title=title);db.add(document);db.flush()
    else: document.title=title
    duplicate=db.query(DocumentVersion).filter(DocumentVersion.document_id==document.id,DocumentVersion.version==version).one_or_none()
    if duplicate is not None: raise DuplicateVersionError(f"Version {version!r} already exists for document {external_id!r}")
    if is_current: db.query(DocumentVersion).filter(DocumentVersion.document_id==document.id,DocumentVersion.is_current.is_(True)).update({DocumentVersion.is_current:False})
    dv=DocumentVersion(document_id=document.id,version=version,source_path=source_path or str(path),is_current=is_current,effective_at=effective_at);db.add(dv);db.flush()
    pending=[]
    for page,text in parse_file(path):pending.extend(chunk_text(text,page=page))
    if not pending: raise ValueError("The document contained no extractable text")
    vectors=embed_texts([x.content for x in pending])
    for item,vector in zip(pending,vectors,strict=True): db.add(Chunk(tenant_id=tenant_id,document_id=document.id,version_id=dv.id,chunk_index=item.index,content=item.content,page=item.page,section=item.section,metadata_json={"source_filename":path.name},embedding=vector))
    db.commit();db.refresh(dv);return dv
