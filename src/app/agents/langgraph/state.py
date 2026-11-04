from typing import TypedDict
from uuid import UUID
from app.retrieval.schemas import Answer, RetrievedChunk
class RAGState(TypedDict,total=False):
    tenant_id:UUID
    question:str
    retrieved:list[RetrievedChunk]
    answer:Answer
    route:str
    guardrail_findings:list[dict]
