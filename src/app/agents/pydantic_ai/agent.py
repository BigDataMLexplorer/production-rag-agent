from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from pydantic_ai import Agent,RunContext
from sqlalchemy.orm import Session
from app.retrieval.search import hybrid_search
@dataclass
class AgentDeps: db:Session; tenant_id:UUID
def build_agent(model:str):
    agent=Agent(model,deps_type=AgentDeps,instructions="You are a tenant-isolated knowledge assistant. Answer only from retrieved evidence. If the evidence is insufficient, say so instead of guessing. Include document/version identifiers from the retrieval tool in your answer.")
    @agent.tool
    def retrieve(ctx:RunContext[AgentDeps],query:str)->str:
        chunks=hybrid_search(ctx.deps.db,tenant_id=ctx.deps.tenant_id,query=query,top_k=5)
        if not chunks:return "NO_EVIDENCE"
        return "\n\n".join(f"SOURCE={c.document_title} VERSION={c.document_version} CHUNK={c.chunk_id}\n{c.content}" for c in chunks)
    return agent
