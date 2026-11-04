from __future__ import annotations
from langgraph.graph import END,START,StateGraph
from sqlalchemy.orm import Session
from app.agents.common import AnswerGenerator
from app.agents.factory import get_answer_generator
from app.agents.langgraph.state import RAGState
from app.guardrails.prompt_injection import filter_suspicious_chunks
from app.retrieval.rerank import rerank
from app.retrieval.search import hybrid_search

def build_rag_graph(db:Session,generator:AnswerGenerator|None=None):
    generator=generator or get_answer_generator()
    def retrieve(state:RAGState)->RAGState: return {"retrieved":hybrid_search(db,tenant_id=state["tenant_id"],query=state["question"],top_k=8)}
    def rerank_node(state:RAGState)->RAGState: return {"retrieved":rerank(state["question"],state.get("retrieved",[]),top_k=4)}
    def guardrail_node(state:RAGState)->RAGState:
        safe,findings=filter_suspicious_chunks(state.get("retrieved",[])); return {"retrieved":safe,"guardrail_findings":[{"chunk_id":x.chunk_id,"matched_patterns":list(x.matched_patterns)} for x in findings]}
    def decide(state:RAGState)->RAGState:return {"route":"answer" if state.get("retrieved",[]) else "escalate"}
    def answer_node(state:RAGState)->RAGState:return {"answer":generator.answer(question=state["question"],context=state.get("retrieved",[]))}
    def escalate(state:RAGState)->RAGState:
        from app.retrieval.schemas import Answer
        reason="all_retrieved_chunks_blocked" if state.get("guardrail_findings") else "low_confidence"
        return {"answer":Answer(answer="I don't have enough safe, grounded evidence. Escalating to a human.",escalated=True,reason=reason)}
    graph=StateGraph(RAGState)
    for n,f in [("retrieve",retrieve),("rerank",rerank_node),("guardrails",guardrail_node),("decide",decide),("answer",answer_node),("escalate",escalate)]:graph.add_node(n,f)
    graph.add_edge(START,"retrieve");graph.add_edge("retrieve","rerank");graph.add_edge("rerank","guardrails");graph.add_edge("guardrails","decide")
    graph.add_conditional_edges("decide",lambda s:s["route"],{"answer":"answer","escalate":"escalate"});graph.add_edge("answer",END);graph.add_edge("escalate",END)
    return graph.compile()
