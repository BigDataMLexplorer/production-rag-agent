# Evaluation plan

The final portfolio must report measured results, never invented claims.

Compare:

1. vector-only retrieval
2. hybrid retrieval
3. hybrid retrieval + cross-encoder reranking

Initial retrieval metrics:

- Hit@K
- MRR
- current-version accuracy
- tenant leakage count (target: zero)

Later generation metrics:

- citation correctness
- groundedness
- answer completeness
- abstention accuracy
- latency
- token usage / estimated model cost
