from uuid import UUID

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    tenant_id: UUID
    chunk_id: UUID
    document_id: UUID
    document_external_id: str
    version_id: UUID
    document_title: str
    document_version: str
    content: str
    page: int | None = None
    section: str | None = None
    score: float
    vector_rank: int | None = None
    keyword_rank: int | None = None
    is_current: bool


class Citation(BaseModel):
    document: str
    version: str
    page: int | None = None
    section: str | None = None
    chunk_id: UUID


class Answer(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    escalated: bool = False
    reason: str | None = None
