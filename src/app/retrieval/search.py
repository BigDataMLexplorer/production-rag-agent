from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.observability.telemetry import tracer
from app.retrieval.embeddings import embed_query
from app.retrieval.schemas import RetrievedChunk

RRF_K = 60.0
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for",
    "from", "how", "i", "in", "is", "it", "of", "on", "or", "our", "the",
    "to", "under", "we", "what", "when", "which", "who", "with",
}
_STRONG_IDENTIFIER = re.compile(
    r"\b(?=[A-Z0-9_]{5,}\b)(?=[A-Z0-9_]*[A-Z]{2})(?=[A-Z0-9_]*\d{2})[A-Z0-9_]+\b"
)


def _row_to_chunk(row) -> RetrievedChunk:
    return RetrievedChunk(
        tenant_id=row.tenant_id,
        chunk_id=row.chunk_id,
        document_id=row.document_id,
        document_external_id=row.document_external_id,
        version_id=row.version_id,
        document_title=row.document_title,
        document_version=row.document_version,
        content=row.content,
        page=row.page,
        section=row.section,
        score=float(row.score),
        vector_rank=getattr(row, "vector_rank", None),
        keyword_rank=getattr(row, "keyword_rank", None),
        is_current=row.is_current,
    )


def build_keyword_query(query: str) -> str:
    """Build a broad lexical query for first-stage candidate generation."""
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_]*", query)
    filtered = [token for token in tokens if token.lower() not in _STOPWORDS and len(token) > 1]
    return " OR ".join(filtered) if filtered else query


def fusion_weights(query: str) -> tuple[float, float]:
    """Choose semantic/lexical RRF weights from query shape.

    Exact enterprise identifiers benefit from lexical matching. Natural-language
    questions remain semantic-first so noisy token overlap cannot overpower a
    strong embedding match.
    """
    if _STRONG_IDENTIFIER.search(query):
        return 0.75, 1.50
    return 1.00, 0.70


def vector_search(db: Session, *, tenant_id: UUID, query: str, top_k: int = 8) -> list[RetrievedChunk]:
    with tracer.start_as_current_span("retrieval.vector") as span:
        span.set_attribute("rag.tenant_id", str(tenant_id))
        span.set_attribute("rag.top_k", top_k)
        embedding = embed_query(query)
    sql = text("""
        SELECT c.tenant_id,c.id AS chunk_id,c.document_id,d.external_id AS document_external_id,
               c.version_id,d.title AS document_title,dv.version AS document_version,c.content,
               c.page,c.section,dv.is_current,
               1-(c.embedding <=> CAST(:embedding AS vector)) AS score
        FROM chunks c
        JOIN documents d ON d.id=c.document_id
        JOIN document_versions dv ON dv.id=c.version_id
        WHERE c.tenant_id=:tenant_id
        ORDER BY CASE WHEN dv.is_current THEN 0 ELSE 1 END,
                 c.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)
    return [
        _row_to_chunk(row)
        for row in db.execute(
            sql,
            {"tenant_id": tenant_id, "embedding": str(embedding), "top_k": top_k},
        )
    ]


def keyword_search(db: Session, *, tenant_id: UUID, query: str, top_k: int = 8) -> list[RetrievedChunk]:
    keyword_query = build_keyword_query(query)
    with tracer.start_as_current_span("retrieval.keyword") as span:
        span.set_attribute("rag.tenant_id", str(tenant_id))
        span.set_attribute("rag.top_k", top_k)
    sql = text("""
        SELECT c.tenant_id,c.id AS chunk_id,c.document_id,d.external_id AS document_external_id,
               c.version_id,d.title AS document_title,dv.version AS document_version,c.content,
               c.page,c.section,dv.is_current,
               ts_rank_cd(c.search_vector, websearch_to_tsquery('english', :keyword_query)) AS score
        FROM chunks c
        JOIN documents d ON d.id=c.document_id
        JOIN document_versions dv ON dv.id=c.version_id
        WHERE c.tenant_id=:tenant_id
          AND c.search_vector @@ websearch_to_tsquery('english', :keyword_query)
        ORDER BY CASE WHEN dv.is_current THEN 0 ELSE 1 END, score DESC
        LIMIT :top_k
    """)
    return [
        _row_to_chunk(row)
        for row in db.execute(
            sql,
            {"tenant_id": tenant_id, "keyword_query": keyword_query, "top_k": top_k},
        )
    ]


def hybrid_search(db: Session, *, tenant_id: UUID, query: str, top_k: int = 8) -> list[RetrievedChunk]:
    keyword_query = build_keyword_query(query)
    vector_weight, keyword_weight = fusion_weights(query)
    with tracer.start_as_current_span("retrieval.hybrid") as span:
        span.set_attribute("rag.tenant_id", str(tenant_id))
        span.set_attribute("rag.top_k", top_k)
        span.set_attribute("rag.vector_weight", vector_weight)
        span.set_attribute("rag.keyword_weight", keyword_weight)
        embedding = embed_query(query)

    sql = text("""
        WITH vector_candidates AS (
          SELECT c.id,
                 row_number() OVER (
                   ORDER BY CASE WHEN dv.is_current THEN 0 ELSE 1 END,
                            c.embedding <=> CAST(:embedding AS vector)
                 ) AS rnk
          FROM chunks c
          JOIN document_versions dv ON dv.id=c.version_id
          WHERE c.tenant_id=:tenant_id
          ORDER BY CASE WHEN dv.is_current THEN 0 ELSE 1 END,
                   c.embedding <=> CAST(:embedding AS vector)
          LIMIT :candidate_k
        ),
        keyword_candidates AS (
          SELECT c.id,
                 row_number() OVER (
                   ORDER BY CASE WHEN dv.is_current THEN 0 ELSE 1 END,
                            ts_rank_cd(
                              c.search_vector,
                              websearch_to_tsquery('english', :keyword_query)
                            ) DESC
                 ) AS rnk
          FROM chunks c
          JOIN document_versions dv ON dv.id=c.version_id
          WHERE c.tenant_id=:tenant_id
            AND c.search_vector @@ websearch_to_tsquery('english', :keyword_query)
          ORDER BY CASE WHEN dv.is_current THEN 0 ELSE 1 END,
                   ts_rank_cd(
                     c.search_vector,
                     websearch_to_tsquery('english', :keyword_query)
                   ) DESC
          LIMIT :candidate_k
        ),
        fused AS (
          SELECT id,
                 MIN(vector_rank) AS vector_rank,
                 MIN(keyword_rank) AS keyword_rank,
                 SUM(score) AS score
          FROM (
            SELECT id,
                   rnk AS vector_rank,
                   NULL::bigint AS keyword_rank,
                   :vector_weight / (:rrf_k + rnk) AS score
            FROM vector_candidates
            UNION ALL
            SELECT id,
                   NULL::bigint,
                   rnk,
                   :keyword_weight / (:rrf_k + rnk) AS score
            FROM keyword_candidates
          ) s
          GROUP BY id
        )
        SELECT c.tenant_id,c.id AS chunk_id,c.document_id,
               d.external_id AS document_external_id,c.version_id,
               d.title AS document_title,dv.version AS document_version,
               c.content,c.page,c.section,dv.is_current,
               f.vector_rank,f.keyword_rank,
               f.score + CASE WHEN dv.is_current THEN 0.01 ELSE 0 END AS score
        FROM fused f
        JOIN chunks c ON c.id=f.id
        JOIN documents d ON d.id=c.document_id
        JOIN document_versions dv ON dv.id=c.version_id
        ORDER BY score DESC
        LIMIT :top_k
    """)
    params = {
        "tenant_id": tenant_id,
        "embedding": str(embedding),
        "keyword_query": keyword_query,
        "candidate_k": max(top_k * 4, 20),
        "top_k": top_k,
        "rrf_k": RRF_K,
        "vector_weight": vector_weight,
        "keyword_weight": keyword_weight,
    }
    return [_row_to_chunk(row) for row in db.execute(sql, params)]
