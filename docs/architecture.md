# Architecture

```mermaid
flowchart LR
    U[User] --> API[FastAPI]
    API --> G[LangGraph workflow]
    G --> R[Hybrid retrieval]
    R --> PG[(PostgreSQL + pgvector)]
    R --> RR[Cross-encoder reranker]
    RR --> G
    G --> LLM[LLM provider / PydanticAI]
    G --> T[Idempotent tools]
    G --> H[Human escalation]
```

## Design decisions

- Tenant filtering is applied inside retrieval, not after retrieval.
- Document versions are explicit entities; current versions are prioritized in ranking.
- Hybrid retrieval uses semantic + PostgreSQL full-text candidates with Reciprocal Rank Fusion.
- Reranking is separated from first-stage retrieval so the three retrieval configurations can be evaluated independently.
- Tool writes use tenant-scoped idempotency keys.
