# Security and reliability controls

This portfolio project is intentionally not presented as a complete security product. It demonstrates concrete controls that can be reviewed and tested.

## Tenant isolation

Every retrieval query is scoped by `tenant_id` inside SQL before chunks are returned. Tenant filtering is not deferred to the LLM.

## Prompt injection

Retrieved documents are treated as untrusted data. The model instruction explicitly says not to follow commands found in retrieved documents. A deterministic pre-generation guardrail filters a small set of high-signal embedded-instruction patterns and records findings for observability.

This heuristic is intentionally described as a safeguard, not a complete prompt-injection solution.

## Citation validation

Model-backed generation returns structured chunk IDs. Any citation not present in the retrieved context causes the answer to be withheld and escalated.

## Abstention and human escalation

The model returns structured confidence plus a `needs_human` flag. Answers below the configured threshold or without valid citations are escalated. A separate LangGraph workflow demonstrates `interrupt()` + checkpoint-based human review and resume.

## Retry-safe side effects

Synthetic support-ticket creation uses a tenant-scoped idempotency key and a database uniqueness constraint, preventing duplicate records when an agent action is retried.
