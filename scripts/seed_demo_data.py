from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.init_db import init_db
from app.db.models import Chunk,Document,DocumentVersion,Tenant
from app.db.session import SessionLocal
from app.ingestion.chunking import chunk_text
from app.ingestion.parsers import parse_file
from app.retrieval.embeddings import embed_texts
ROOT=Path(__file__).resolve().parents[1];TENANTS={"acme":"Acme Cloud","northstar":"Northstar Analytics"}
def ingest_version(db:Session,*,tenant:Tenant,external_id:str,title:str,version:str,path:Path,is_current:bool,effective_at:datetime)->None:
    document=db.query(Document).filter(Document.tenant_id==tenant.id,Document.external_id==external_id).one_or_none()
    if document is None:document=Document(tenant_id=tenant.id,external_id=external_id,title=title);db.add(document);db.flush()
    if is_current:db.query(DocumentVersion).filter(DocumentVersion.document_id==document.id).update({DocumentVersion.is_current:False})
    dv=DocumentVersion(document_id=document.id,version=version,source_path=str(path.relative_to(ROOT)),is_current=is_current,effective_at=effective_at);db.add(dv);db.flush();pending=[]
    for page,text in parse_file(path):pending.extend(chunk_text(text,page=page))
    vectors=embed_texts([c.content for c in pending])
    for chunk,vector in zip(pending,vectors,strict=True):db.add(Chunk(tenant_id=tenant.id,document_id=document.id,version_id=dv.id,chunk_index=chunk.index,content=chunk.content,page=chunk.page,section=chunk.section,embedding=vector))
def main()->None:
    init_db();db=SessionLocal()
    try:
        tenants={}
        for slug,name in TENANTS.items():
            tenant=db.query(Tenant).filter(Tenant.slug==slug).one_or_none()
            if tenant is None:tenant=Tenant(slug=slug,name=name);db.add(tenant);db.flush()
            tenants[slug]=tenant
        ingest_version(db,tenant=tenants["acme"],external_id="data-retention-policy",title="Data Retention Policy",version="2025-01",path=ROOT/"data/synthetic/acme/data_retention_2025.md",is_current=False,effective_at=datetime(2025,1,1,tzinfo=timezone.utc))
        ingest_version(db,tenant=tenants["acme"],external_id="data-retention-policy",title="Data Retention Policy",version="2026-10",path=ROOT/"data/synthetic/acme/data_retention_2026.md",is_current=True,effective_at=datetime(2026,10,1,tzinfo=timezone.utc))
        ingest_version(db,tenant=tenants["northstar"],external_id="data-retention-policy",title="Data Retention Policy",version="2026-09",path=ROOT/"data/synthetic/northstar/data_retention_2026.md",is_current=True,effective_at=datetime(2026,9,1,tzinfo=timezone.utc));db.commit();print("Synthetic demo data seeded.")
        for slug,tenant in tenants.items():print(f"{slug}: tenant_id={tenant.id}")
    finally:db.close()
if __name__=="__main__":main()
