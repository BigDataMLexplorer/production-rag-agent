from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.models import Chunk, Document, DocumentVersion, Tenant
from app.db.session import SessionLocal
from app.ingestion.chunking import chunk_text
from app.ingestion.parsers import parse_file
from app.retrieval.embeddings import embed_texts

ROOT = Path(__file__).resolve().parents[1]
TENANTS = {"acme": "Acme Cloud", "northstar": "Northstar Analytics"}


def _get_or_create_document(db: Session, *, tenant: Tenant, external_id: str, title: str) -> Document:
    document = db.query(Document).filter(
        Document.tenant_id == tenant.id, Document.external_id == external_id
    ).one_or_none()
    if document is None:
        document = Document(tenant_id=tenant.id, external_id=external_id, title=title)
        db.add(document)
        db.flush()
    else:
        document.title = title
    return document


def _version_exists(db: Session, *, document: Document, version: str) -> bool:
    return db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document.id,
        DocumentVersion.version == version,
    ).one_or_none() is not None


def _promote_current(db: Session, *, document: Document) -> None:
    db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document.id,
        DocumentVersion.is_current.is_(True),
    ).update({DocumentVersion.is_current: False})


def _store_chunks(
    db: Session,
    *,
    tenant: Tenant,
    document: Document,
    document_version: DocumentVersion,
    texts: list[tuple[int | None, str]],
    source_name: str,
) -> None:
    pending = []
    for page, text in texts:
        pending.extend(chunk_text(text, page=page))
    if not pending:
        return
    vectors = embed_texts([chunk.content for chunk in pending])
    for chunk, vector in zip(pending, vectors, strict=True):
        db.add(Chunk(
            tenant_id=tenant.id,
            document_id=document.id,
            version_id=document_version.id,
            chunk_index=chunk.index,
            content=chunk.content,
            page=chunk.page,
            section=chunk.section,
            metadata_json={"source": source_name},
            embedding=vector,
        ))


def ingest_file_version(
    db: Session, *, tenant: Tenant, external_id: str, title: str,
    version: str, path: Path, is_current: bool, effective_at: datetime,
) -> None:
    document = _get_or_create_document(
        db, tenant=tenant, external_id=external_id, title=title
    )
    if _version_exists(db, document=document, version=version):
        return
    if is_current:
        _promote_current(db, document=document)
    dv = DocumentVersion(
        document_id=document.id,
        version=version,
        source_path=str(path.relative_to(ROOT)),
        is_current=is_current,
        effective_at=effective_at,
    )
    db.add(dv)
    db.flush()
    _store_chunks(
        db,
        tenant=tenant,
        document=document,
        document_version=dv,
        texts=parse_file(path),
        source_name=path.name,
    )


def ingest_text_version(
    db: Session, *, tenant: Tenant, external_id: str, title: str,
    version: str, text: str, is_current: bool,
) -> None:
    document = _get_or_create_document(
        db, tenant=tenant, external_id=external_id, title=title
    )
    if _version_exists(db, document=document, version=version):
        return
    if is_current:
        _promote_current(db, document=document)
    dv = DocumentVersion(
        document_id=document.id,
        version=version,
        source_path="synthetic://additional_policies.json",
        is_current=is_current,
    )
    db.add(dv)
    db.flush()
    _store_chunks(
        db,
        tenant=tenant,
        document=document,
        document_version=dv,
        texts=[(None, text)],
        source_name="additional_policies.json",
    )


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        tenants: dict[str, Tenant] = {}
        for slug, name in TENANTS.items():
            tenant = db.query(Tenant).filter(Tenant.slug == slug).one_or_none()
            if tenant is None:
                tenant = Tenant(slug=slug, name=name)
                db.add(tenant)
                db.flush()
            tenants[slug] = tenant

        ingest_file_version(
            db,
            tenant=tenants["acme"],
            external_id="data-retention-policy",
            title="Data Retention Policy",
            version="2025-01",
            path=ROOT / "data/synthetic/acme/data_retention_2025.md",
            is_current=False,
            effective_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        ingest_file_version(
            db,
            tenant=tenants["acme"],
            external_id="data-retention-policy",
            title="Data Retention Policy",
            version="2026-10",
            path=ROOT / "data/synthetic/acme/data_retention_2026.md",
            is_current=True,
            effective_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        )
        ingest_file_version(
            db,
            tenant=tenants["northstar"],
            external_id="data-retention-policy",
            title="Data Retention Policy",
            version="2026-09",
            path=ROOT / "data/synthetic/northstar/data_retention_2026.md",
            is_current=True,
            effective_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )

        policies = json.loads(
            (ROOT / "data/synthetic/additional_policies.json").read_text(encoding="utf-8")
        )
        for item in policies:
            ingest_text_version(
                db,
                tenant=tenants[item["tenant"]],
                external_id=item["external_id"],
                title=item["title"],
                version=item["version"],
                text=item["text"],
                is_current=item["is_current"],
            )

        db.commit()
        print(f"Synthetic demo data seeded ({len(policies) + 3} document versions).")
        for slug, tenant in tenants.items():
            print(f"{slug}: tenant_id={tenant.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
