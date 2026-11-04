from uuid import uuid4

from app.retrieval import rerank as rerank_module
from app.retrieval.schemas import RetrievedChunk


class FakeReranker:
    def predict(self, pairs):
        # Deliberately gives the stale chunk a much higher relevance score.
        return [0.99, 0.50]


def _chunk(*, version: str, is_current: bool) -> RetrievedChunk:
    return RetrievedChunk(
        tenant_id=uuid4(),
        chunk_id=uuid4(),
        document_id=uuid4(),
        document_external_id="backup-recovery",
        version_id=uuid4(),
        document_title="Backup and Recovery Standard",
        document_version=version,
        content="Nightly backups are retained for a configured period.",
        score=0.5,
        is_current=is_current,
    )


def test_reranker_cannot_promote_superseded_version(monkeypatch) -> None:
    stale = _chunk(version="2025-06", is_current=False)
    current = _chunk(version="2026-08", is_current=True)
    monkeypatch.setattr(rerank_module, "get_reranker", lambda: FakeReranker())

    ranked = rerank_module.rerank("How long are nightly backups retained?", [stale, current])

    assert ranked[0].document_version == "2026-08"
    assert ranked[0].is_current is True
