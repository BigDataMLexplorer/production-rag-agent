from app.retrieval.search import build_keyword_query


def test_keyword_query_turns_natural_language_into_broad_or_query() -> None:
    assert build_keyword_query(
        "How long are application logs kept by default?"
    ) == "long OR application OR logs OR kept OR default"


def test_keyword_query_preserves_exact_reference_identifier() -> None:
    assert "RET90A" in build_keyword_query("What requirement is identified by RET90A?")
