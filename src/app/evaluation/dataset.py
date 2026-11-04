import json
from pathlib import Path

from pydantic import BaseModel


class RetrievalCase(BaseModel):
    tenant: str
    question: str
    expected_document_external_id: str
    expected_version: str
    category: str = "semantic"


def load_cases(path: Path) -> list[RetrievalCase]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [RetrievalCase.model_validate(item) for item in data]
