from typing import Protocol

from app.retrieval.schemas import Answer, RetrievedChunk


class AnswerGenerator(Protocol):
    def answer(self, *, question: str, context: list[RetrievedChunk]) -> Answer: ...


class ExtractiveDemoGenerator:
    """No-API fallback used for local smoke tests and screenshots of retrieval behavior."""

    def answer(self, *, question: str, context: list[RetrievedChunk]) -> Answer:
        if not context:
            return Answer(
                answer="I don't have enough grounded evidence to answer this question.",
                escalated=True,
                reason="no_relevant_context",
            )
        best = context[0]
        body_lines = [
            line.strip()
            for line in best.content.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        body = " ".join(body_lines) or best.content.strip()
        sentence = body.split(".")[0].strip()
        from app.retrieval.schemas import Citation

        return Answer(
            answer=sentence + ".",
            citations=[
                Citation(
                    document=best.document_title,
                    version=best.document_version,
                    page=best.page,
                    section=best.section,
                    chunk_id=best.chunk_id,
                )
            ],
        )
