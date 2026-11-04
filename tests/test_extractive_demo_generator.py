from uuid import uuid4

from app.agents.common import ExtractiveDemoGenerator
from app.retrieval.schemas import RetrievedChunk


def test_extractive_demo_generator_skips_markdown_heading() -> None:
    tenant_id = uuid4()
    chunk = RetrievedChunk(
        tenant_id=tenant_id,
        chunk_id=uuid4(),
        document_id=uuid4(),
        document_external_id="retention",
        version_id=uuid4(),
        document_title="Data Retention Policy",
        document_version="2026-10",
        content="# Data Retention Policy\nCustomer application logs are retained for 90 days by default.",
        score=1.0,
        is_current=True,
    )

    answer = ExtractiveDemoGenerator().answer(
        question="How long are application logs retained?",
        context=[chunk],
    )

    assert answer.answer == "Customer application logs are retained for 90 days by default."
    assert answer.citations[0].version == "2026-10"
