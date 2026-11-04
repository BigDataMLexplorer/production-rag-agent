from datetime import datetime,timezone
from uuid import uuid4
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.models import Chunk,Document,DocumentVersion,Tenant
from app.retrieval import search as search_module
pytestmark=pytest.mark.integration
def unit_vector(index:int)->list[float]:
    values=[0.0]*384;values[index]=1.0;return values
def test_hybrid_search_enforces_tenant_and_prefers_current(monkeypatch)->None:
    from app.core.config import get_settings
    engine=create_engine(get_settings().database_url);monkeypatch.setattr(search_module,"embed_query",lambda _:unit_vector(0))
    with Session(engine) as db:
        acme=Tenant(id=uuid4(),slug=f"acme-{uuid4().hex[:8]}",name="Acme");north=Tenant(id=uuid4(),slug=f"north-{uuid4().hex[:8]}",name="Northstar");db.add_all([acme,north]);db.flush()
        ad=Document(tenant_id=acme.id,external_id="retention",title="Data Retention");nd=Document(tenant_id=north.id,external_id="retention",title="Data Retention");db.add_all([ad,nd]);db.flush()
        old=DocumentVersion(document_id=ad.id,version="2025-01",source_path="old.md",is_current=False,effective_at=datetime(2025,1,1,tzinfo=timezone.utc));cur=DocumentVersion(document_id=ad.id,version="2026-10",source_path="current.md",is_current=True,effective_at=datetime(2026,10,1,tzinfo=timezone.utc));other=DocumentVersion(document_id=nd.id,version="2026-09",source_path="north.md",is_current=True,effective_at=datetime(2026,9,1,tzinfo=timezone.utc));db.add_all([old,cur,other]);db.flush()
        db.add_all([Chunk(tenant_id=acme.id,document_id=ad.id,version_id=old.id,chunk_index=0,content="Application logs are retained for 365 days.",metadata_json={},embedding=unit_vector(0)),Chunk(tenant_id=acme.id,document_id=ad.id,version_id=cur.id,chunk_index=0,content="Application logs are retained for 90 days.",metadata_json={},embedding=unit_vector(0)),Chunk(tenant_id=north.id,document_id=nd.id,version_id=other.id,chunk_index=0,content="Application logs are retained for 24 months.",metadata_json={},embedding=unit_vector(0))]);db.commit()
        results=search_module.hybrid_search(db,tenant_id=acme.id,query="application logs retained",top_k=10);assert results;assert all(x.tenant_id==acme.id for x in results);assert results[0].document_version=="2026-10";assert "90 days" in results[0].content
