from app.evaluation.metrics import hit_at_k,reciprocal_rank
def test_reciprocal_rank()->None:
    assert reciprocal_rank(["a","b","c"],"b")==.5;assert reciprocal_rank(["a","b"],"x")==0.0
def test_hit_at_k()->None:
    assert hit_at_k(["a","b","c"],"b",2)==1.0;assert hit_at_k(["a","b","c"],"c",2)==0.0
