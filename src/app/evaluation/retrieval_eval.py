from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from time import perf_counter
from math import ceil

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Tenant
from app.evaluation.dataset import RetrievalCase, load_cases
from app.evaluation.metrics import hit_at_k, mean, reciprocal_rank
from app.retrieval.embeddings import embed_query
from app.retrieval.rerank import get_reranker, rerank
from app.retrieval.schemas import RetrievedChunk
from app.retrieval.search import hybrid_search, vector_search


@dataclass
class CaseResult:
    mode: str
    tenant: str
    question: str
    expected_document_external_id: str
    expected_version: str
    top_document_external_id: str | None
    top_version: str | None
    hit_at_1: float
    hit_at_3: float
    mrr: float
    current_version_correct: float
    tenant_leakage_count: int
    latency_ms: float


@dataclass
class ModeSummary:
    mode: str
    cases: int
    hit_at_1: float
    hit_at_3: float
    mrr: float
    current_version_accuracy: float
    tenant_leakage_count: int
    mean_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float


def _identity(chunk: RetrievedChunk) -> str:
    return f"{chunk.document_external_id}::{chunk.document_version}"


def _run_mode(
    db: Session,
    *,
    case: RetrievalCase,
    tenant: Tenant,
    mode: str,
) -> CaseResult:
    settings = get_settings()
    started = perf_counter()

    if mode == "vector":
        chunks = vector_search(db, tenant_id=tenant.id, query=case.question, top_k=settings.rag_top_k)
    elif mode == "hybrid":
        chunks = hybrid_search(db, tenant_id=tenant.id, query=case.question, top_k=settings.rag_top_k)
    elif mode == "hybrid_rerank":
        first_stage = hybrid_search(
            db,
            tenant_id=tenant.id,
            query=case.question,
            top_k=settings.rag_top_k,
        )
        chunks = rerank(case.question, first_stage, top_k=settings.rag_rerank_top_k)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    latency_ms = (perf_counter() - started) * 1000
    expected_identity = f"{case.expected_document_external_id}::{case.expected_version}"
    ranked = [_identity(chunk) for chunk in chunks]
    leakage = sum(chunk.tenant_id != tenant.id for chunk in chunks)
    top = chunks[0] if chunks else None

    return CaseResult(
        mode=mode,
        tenant=case.tenant,
        question=case.question,
        expected_document_external_id=case.expected_document_external_id,
        expected_version=case.expected_version,
        top_document_external_id=top.document_external_id if top else None,
        top_version=top.document_version if top else None,
        hit_at_1=hit_at_k(ranked, expected_identity, 1),
        hit_at_3=hit_at_k(ranked, expected_identity, 3),
        mrr=reciprocal_rank(ranked, expected_identity),
        current_version_correct=float(bool(top) and top.document_version == case.expected_version),
        tenant_leakage_count=leakage,
        latency_ms=latency_ms,
    )


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, ceil(percentile * len(ordered)) - 1))
    return ordered[index]


def _warm_up_models(modes: tuple[str, ...]) -> None:
    # Exclude one-time model loading from steady-state request latency.
    embed_query("benchmark warmup")
    if "hybrid_rerank" in modes:
        get_reranker().predict([("benchmark warmup", "benchmark warmup")])


def run_retrieval_evaluation(
    db: Session,
    dataset_path: Path,
    modes: tuple[str, ...] = ("vector", "hybrid", "hybrid_rerank"),
) -> tuple[list[CaseResult], list[ModeSummary]]:
    cases = load_cases(dataset_path)
    _warm_up_models(modes)
    cache: dict[str, Tenant] = {}
    results: list[CaseResult] = []

    for case in cases:
        tenant = cache.get(case.tenant)
        if tenant is None:
            tenant = db.query(Tenant).filter(Tenant.slug == case.tenant).one()
            cache[case.tenant] = tenant
        for mode in modes:
            results.append(_run_mode(db, case=case, tenant=tenant, mode=mode))

    summaries: list[ModeSummary] = []
    for mode in modes:
        sub = [r for r in results if r.mode == mode]
        latencies = [r.latency_ms for r in sub]
        summaries.append(
            ModeSummary(
                mode=mode,
                cases=len(sub),
                hit_at_1=mean([r.hit_at_1 for r in sub]),
                hit_at_3=mean([r.hit_at_3 for r in sub]),
                mrr=mean([r.mrr for r in sub]),
                current_version_accuracy=mean([r.current_version_correct for r in sub]),
                tenant_leakage_count=sum(r.tenant_leakage_count for r in sub),
                mean_latency_ms=mean(latencies),
                p50_latency_ms=_percentile(latencies, 0.50),
                p95_latency_ms=_percentile(latencies, 0.95),
            )
        )
    return results, summaries


def serialize_results(results: list[CaseResult], summaries: list[ModeSummary]) -> dict:
    return {
        "cases": [asdict(item) for item in results],
        "summary": [asdict(item) for item in summaries],
    }
