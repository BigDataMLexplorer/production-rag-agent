# Production Multi-Tenant RAG Agent

A public, independently created portfolio project demonstrating production-oriented RAG and agent engineering with **FastAPI, PostgreSQL/pgvector, LangGraph and PydanticAI**.

> This repository uses only synthetic data. It contains no employer/client code, architecture, documents or datasets.

## Why this project exists

The goal is to demonstrate more than a "chat with PDF" demo. The system focuses on problems that matter in production:

- tenant-isolated retrieval
- explicit document versioning
- hybrid semantic + keyword retrieval
- reranking
- source-grounded responses
- retry-safe / idempotent agent tools
- human escalation
- evaluation and observability

## Architecture

See [`docs/architecture.md`](docs/architecture.md).

## Current implementation

- FastAPI service with `/chat`, `/retrieve`, `/documents/ingest`, `/tenants`, and `/health` endpoints
- lightweight demo UI at `/demo` for portfolio screenshots
- PostgreSQL + pgvector Docker service
- Alembic database migrations
- HNSW vector index + generated PostgreSQL `tsvector`/GIN index
- tenant / document / version / chunk / tool-execution data model
- local SentenceTransformers embeddings
- vector-only and keyword-only baselines
- query-adaptive PostgreSQL full-text + pgvector hybrid retrieval with weighted RRF
- current-document version priority preserved through reranking
- cross-encoder reranking
- LangGraph RAG workflow
- structured model-backed grounded generation through PydanticAI (when `LLM_MODEL` is configured)
- confidence-based abstention and citation validation
- LangGraph human-review interrupt/resume workflow
- prompt-injection safeguards for retrieved documents
- PydanticAI agent variant with tenant-scoped retrieval tool
- idempotent synthetic `create_support_ticket` tool
- OpenTelemetry-ready FastAPI and retrieval tracing
- PDF, DOCX, Markdown and text parsers
- upload-driven ingestion with explicit document versions and current-version promotion
- synthetic multi-tenant dataset with deliberately stale document versions
- retrieval evaluation split into semantic, exact-identifier and ambiguous query categories
- live browser screenshot captured from the running FastAPI demo in CI

## Quick start

```bash
cp .env.example .env
docker compose up -d postgres
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
PYTHONPATH=src python scripts/seed_demo_data.py
uvicorn app.main:app --reload
```

Then open `http://localhost:8000/docs` for the API or `http://localhost:8000/demo` for the portfolio demo UI.

## Run tests

```bash
pytest -q
```

## Run retrieval evaluation

After seeding the database:

```bash
PYTHONPATH=src python scripts/run_retrieval_evaluation.py
PYTHONPATH=src python scripts/plot_retrieval_evaluation.py
```

### Measured retrieval result

On the checked-in **34-question** synthetic benchmark:

| Pipeline | Hit@1 | Hit@3 | MRR | p50 latency | p95 latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| Vector | 94.12% | 94.12% | 0.9520 | 12.2 ms | 16.2 ms |
| Keyword | 94.12% | 100% | 0.9706 | 0.9 ms | 1.7 ms |
| Adaptive hybrid | **97.06%** | **100%** | **0.9853** | 12.0 ms | 19.1 ms |
| Hybrid + reranker | **100%** | **100%** | **1.0000** | 89.2 ms | 109.9 ms |

All four pipelines produced **zero cross-tenant leakage** in the benchmark.

The category split explains why hybrid search helps:

- semantic questions: vector **100% Hit@1**, keyword **90.48%**
- exact-reference-ID questions: vector **81.82%**, keyword **100%**
- adaptive hybrid keeps **100%** on semantic questions while improving exact-ID retrieval to **90.91%**
- the cross-encoder reranker reaches **100% Hit@1 in every benchmark category**

See [`docs/evaluation-results.md`](docs/evaluation-results.md) for methodology, failure analysis and limitations.

## Synthetic versioning scenario

Acme Cloud has two versions of the same data-retention policy:

- stale `2025-01`: application logs retained for **365 days**
- current `2026-10`: application logs retained for **90 days**

Northstar Analytics has a different tenant-only policy. Retrieval must not leak it into Acme responses.

## LangGraph vs. PydanticAI

LangGraph is the primary workflow implementation because it exposes routing and multi-step orchestration explicitly. PydanticAI is included as a typed Python-native alternative rather than forcing both frameworks into the same execution path.

## Model-backed generation

Set `LLM_MODEL` to any PydanticAI-supported model identifier. If no model is configured, the project intentionally falls back to a deterministic extractive demo generator so retrieval can still be exercised without paid API access.

## Human-in-the-loop

`/chat/reviewable` runs a LangGraph workflow with a checkpointer. Low-confidence/unsafe answers pause at `interrupt()` for human review and can be resumed through `/chat/reviewable/{thread_id}/resume`. The local demo uses an in-memory checkpointer; a production deployment should use durable persistence.

See [`docs/security.md`](docs/security.md) for the implemented controls and their limitations.

See [`docs/database.md`](docs/database.md) for database/index design.

See [`docs/portfolio-assets.md`](docs/portfolio-assets.md) for the final Upwork screenshot/Loom plan.
