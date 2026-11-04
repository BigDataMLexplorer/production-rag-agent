from __future__ import annotations
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END,START,StateGraph
from langgraph.types import Command,interrupt
from sqlalchemy.orm import Session
from app.agents.factory import get_answer_generator
from app.agents.langgraph.state import RAGState
from app.guardrails.prompt_injection import filter_suspicious_chunks
from app.retrieval.rerank import rerank
from app.retrieval.schemas import Answer
from app.retrieval.search import hybrid_search
_CHECKPOINTER=MemorySaver()
def build_reviewable_graph(db:Session):
    generator=get_answer_generator()
    def retrieve(state:RAGState)->RAGState:
        chunks=rerank(state["question"],hybrid_search(db,tenant_id=state["tenant_id"],query=state["question"],top_k=8),top_k=4);safe,findings=filter_suspicious_chunks(chunks);return {"retrieved":safe,"guardrail_findings":[{"chunk_id":x.chunk_id,"matched_patterns":list(x.matched_patterns)} for x in findings]}
    def draft(state:RAGState)->RAGState:return {"answer":generator.answer(question=state["question"],context=state.get("retrieved",[]))}
    def human_review(state:RAGState):
        answer=state["answer"];decision=interrupt({"question":state["question"],"draft_answer":answer.model_dump(mode="json"),"sources":[c.model_dump(mode="json") for c in state.get("retrieved",[])],"action":"Approve, edit, or reject the escalated answer."})
        if decision.get("approved"):return {"answer":Answer(answer=decision.get("edited_answer") or answer.answer,citations=answer.citations,escalated=False,reason="human_approved")}
        return {"answer":Answer(answer=decision.get("edited_answer") or "A human reviewer rejected the draft answer.",escalated=True,reason="human_rejected")}
    graph=StateGraph(RAGState);graph.add_node("retrieve",retrieve);graph.add_node("draft",draft);graph.add_node("human_review",human_review);graph.add_node("finish",lambda state:{})
    graph.add_edge(START,"retrieve");graph.add_edge("retrieve","draft");graph.add_conditional_edges("draft",lambda s:"human_review" if s["answer"].escalated else "finish",{"human_review":"human_review","finish":"finish"});graph.add_edge("human_review",END);graph.add_edge("finish",END)
    return graph.compile(checkpointer=_CHECKPOINTER)
def resume_review(graph,*,thread_id:str,decision:dict):return graph.invoke(Command(resume=decision),config={"configurable":{"thread_id":thread_id}})
