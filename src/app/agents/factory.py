from app.agents.common import AnswerGenerator, ExtractiveDemoGenerator
from app.agents.model_generator import PydanticAIAnswerGenerator
from app.core.config import get_settings

def get_answer_generator() -> AnswerGenerator:
    settings=get_settings()
    if settings.llm_model:
        return PydanticAIAnswerGenerator(settings.llm_model)
    return ExtractiveDemoGenerator()
