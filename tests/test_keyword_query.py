from app.retrieval.search import build_keyword_query, fusion_weights


def test_keyword_query_turns_natural_language_into_broad_or_query() -> None:
    assert build_keyword_query(
        "How long are application logs kept by default?"
    ) == "long OR application OR logs OR kept OR default"


def test_keyword_query_preserves_exact_reference_identifier() -> None:
    assert "RET90A" in build_keyword_query("What requirement is identified by RET90A?")


def test_fusion_is_semantic_first_for_natural_language() -> None:
    vector_weight, keyword_weight = fusion_weights(
        "Which protocol protects customer data while it is moving across the network?"
    )
    assert vector_weight > keyword_weight


def test_fusion_is_lexical_first_for_strong_identifier() -> None:
    vector_weight, keyword_weight = fusion_weights(
        "What requirement is identified by RET90A?"
    )
    assert keyword_weight > vector_weight
