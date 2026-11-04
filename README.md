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

## Current milestone

Implemented in the initial scaffold:

- FastAPI service with `/chat`, `/retrieve`, `/documents/ingest`, `/tenants`, and `/health` endpoints
- lightweight demo UI at `/demo` for portfolio screenshots
- PostgreSQL + pgvector Docker service
- Alembic database migrations
- HNSW vector index + generated PostgreSQL `tsvector`/GIN index
- tenant / document / version / chunk / tool-execution data model
- local SentenceTransformers embeddings
- vector-only retrieval
- PostgreSQL full-text + vector hybrid retrieval with RRF
- current-document version priority
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
- retrieval evaluation runner comparing vector-only, hybrid, and hybrid + reranker
- retrieval evaluation primitives and contract tests

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

The Swagger UI exposes ingestion, retrieval, standard chat, and reviewable human-in-the-loop chat APIs, so the complete demo can be exercised without a custom frontend.

The seed script prints tenant UUIDs. Use one in `POST /chat`.

## Observability

The API is instrumented with OpenTelemetry. Set `OTEL_EXPORTER_OTLP_ENDPOINT` to export traces to any OTLP-compatible backend, or set `OTEL_CONSOLE_EXPORTER=true` for local trace output. Retrieval spans include tenant and top-k metadata, but not raw document content.

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

The evaluation writes measured results to `artifacts/retrieval_evaluation.json`. These metrics are intentionally generated at runtime; the repository does not ship with fabricated benchmark numbers.

## Synthetic versioning scenario

Acme Cloud has two versions of the same data-retention policy:

- stale `2025-01`: application logs retained for **365 days**
- current `2026-10`: application logs retained for **90 days**

Northstar Analytics has a different tenant-only policy. Retrieval must not leak it into Acme responses.

This lets the project measure two common production failure modes:

1. stale-document retrieval
2. cross-tenant leakage

## LangGraph vs. PydanticAI

LangGraph is the primary workflow implementation because it exposes routing and multi-step orchestration explicitly. PydanticAI is included as a typed Python-native alternative rather than forcing both frameworks into the same execution path.

## Next milestones

- add Alembic migrations and DB integration tests
- add ingestion API + background queue
- add model-backed grounded answer generation
- add confidence/abstention policy
- add human-in-the-loop checkpointing
- add OpenTelemetry traces
- implement full evaluation runner and charts
- add prompt-injection test cases
- create portfolio screenshots and architecture visual

## Model-backed generation

Set `LLM_MODEL` to any PydanticAI-supported model identifier. For example, an AWS Bedrock model can be configured with a `bedrock:` model identifier. If no model is configured, the project intentionally falls back to a deterministic extractive demo generator so retrieval can still be exercised without paid API access.

The model returns structured answer text, cited chunk IDs, confidence and an escalation flag. Citations are validated against the retrieved context before an answer is exposed.

## Human-in-the-loop

`/chat/reviewable` runs a LangGraph workflow with a checkpointer. Low-confidence/unsafe answers pause at `interrupt()` for human review and can be resumed through `/chat/reviewable/{thread_id}/resume`. The local demo uses an in-memory checkpointer; a production deployment should use durable persistence.

See [`docs/security.md`](docs/security.md) for the implemented controls and their limitations.

See [`docs/database.md`](docs/database.md) for database/index design.

See [`docs/portfolio-assets.md`](docs/portfolio-assets.md) for the final Upwork screenshot/Loom plan.
