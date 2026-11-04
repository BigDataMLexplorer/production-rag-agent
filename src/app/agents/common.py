from typing import Protocol

from app.retrieval.schemas import Answer, RetrievedChunk

class AnswerGenerator(Protocol):
    def answer(self, *, question: str, context: list[RetrievedChunk]) -> Answer: ...

class ExtractiveDemoGenerator:
    def answer(self, *, question: str, context: list[RetrievedChunk]) -> Answer:
        if not context:
            return Answer(answer="I don't have enough grounded evidence to answer this question.",escalated=True,reason="no_relevant_context")
        best=context[0]
        sentence=best.content.split(".")[0].strip()
        from app.retrieval.schemas import Citation
        return Answer(answer=sentence+".",citations=[Citation(document=best.document_title,version=best.document_version,page=best.page,section=best.section,chunk_id=best.chunk_id)])
