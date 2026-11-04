from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.core.config import get_settings
from app.retrieval.schemas import RetrievedChunk


@lru_cache
def get_reranker() -> CrossEncoder:
    return CrossEncoder(get_settings().reranker_model)


def rerank(query: str, chunks: list[RetrievedChunk], top_k: int = 4) -> list[RetrievedChunk]:
    if not chunks:
        return []
    scores = get_reranker().predict([(query, chunk.content) for chunk in chunks])

    # A relevance model must not silently promote a superseded version above
    # current knowledge. Historical retrieval can be a separate explicit mode.
    ranked = sorted(
        zip(chunks, scores, strict=True),
        key=lambda pair: (not pair[0].is_current, -float(pair[1])),
    )
    return [
        chunk.model_copy(update={"score": float(score)})
        for chunk, score in ranked[:top_k]
    ]
