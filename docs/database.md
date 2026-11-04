# Database design

## PostgreSQL + pgvector

The schema is managed with Alembic migrations.

```bash
alembic upgrade head
```

### Retrieval indexes

- `chunks.embedding`: HNSW index using cosine distance via pgvector.
- `chunks.search_vector`: persisted generated `tsvector` column with a GIN index.
- tenant/document/version foreign-key columns are indexed for filtering and joins.

Hybrid retrieval combines vector and PostgreSQL full-text rankings with Reciprocal Rank Fusion (RRF), then optionally applies a cross-encoder reranker.

### Why tenant filtering happens in SQL

The database query includes `tenant_id` before candidate retrieval. This prevents chunks from another tenant entering the prompt, rather than relying on an LLM to ignore unauthorized evidence after retrieval.
