from collections.abc import Sequence


def reciprocal_rank(ranked_ids: Sequence[str], expected_id: str) -> float:
    for index, item in enumerate(ranked_ids, start=1):
        if item == expected_id:
            return 1.0 / index
    return 0.0


def hit_at_k(ranked_ids: Sequence[str], expected_id: str, k: int) -> float:
    return float(expected_id in ranked_ids[:k])


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0
