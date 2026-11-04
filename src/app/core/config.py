from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://rag:rag@localhost:5432/rag"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    embedding_dimension: int = 384
    rag_top_k: int = 8
    rag_rerank_top_k: int = 4
    llm_model: str | None = None
    rag_min_confidence: float = 0.65


@lru_cache
def get_settings() -> Settings:
    return Settings()
