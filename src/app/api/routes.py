from __future__ import annotations
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID
from fastapi import APIRouter,Depends,File,Form,HTTPException,UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.agents.langgraph.workflow import build_rag_graph
from app.agents.langgraph.review_workflow import build_reviewable_graph,resume_review
from app.api.schemas import ChatRequest,ChatResponse,IngestionResponse,RetrievalRequest,RetrievalResponse,ReviewableChatRequest,ReviewDecision
from app.db.models import Tenant
from app.db.session import get_db
from app.ingestion.service import DuplicateVersionError,ingest_file
from app.retrieval.rerank import rerank
from app.retrieval.search import hybrid_search
router=APIRouter(); WEB_ROOT=Path(__file__).resolve().parents[1]/"web"
@router.get("/demo",response_class=HTMLResponse,include_in_schema=False)
def demo_page()->HTMLResponse:return HTMLResponse((WEB_ROOT/"demo.html").read_text(encoding="utf-8"))
@router.get("/health")
def health()->dict[str,str]:return {"status":"ok"}
@router.get("/tenants")
def list_tenants(db:Session=Depends(get_db))->list[dict[str,str]]:
    tenants=db.query(Tenant).order_by(Tenant.slug).all(); return [{"id":str(x.id),"slug":x.slug,"name":x.name} for x in tenants]
@router.post("/documents/ingest",response_model=IngestionResponse)
def ingest_document(tenant_id:UUID=Form(...),external_id:str=Form(...),title:str=Form(...),version:str=Form(...),is_current:bool=Form(True),effective_at:datetime|None=Form(None),file:UploadFile=File(...),db:Session=Depends(get_db))->IngestionResponse:
    if db.get(Tenant,tenant_id) is None: raise HTTPException(status_code=404,detail="Tenant not found")
    suffix=Path(file.filename or "upload.txt").suffix.lower()
    if suffix not in {".txt",".md",".pdf",".docx"}: raise HTTPException(status_code=415,detail="Supported types: txt, md, pdf, docx")
    with TemporaryDirectory() as tmp:
        path=Path(tmp)/f"upload{suffix}"; path.write_bytes(file.file.read())
        try: dv=ingest_file(db,tenant_id=tenant_id,external_id=external_id,title=title,version=version,path=path,is_current=is_current,effective_at=effective_at,source_path=f"upload://{file.filename or path.name}")
        except DuplicateVersionError as exc: db.rollback(); raise HTTPException(status_code=409,detail=str(exc)) from exc
        except ValueError as exc: db.rollback(); raise HTTPException(status_code=422,detail=str(exc)) from exc
    return IngestionResponse(document_version_id=dv.id,version=dv.version,is_current=dv.is_current)
@router.post("/retrieve",response_model=RetrievalResponse)
def retrieve(payload:RetrievalRequest,db:Session=Depends(get_db))->RetrievalResponse:
    chunks=hybrid_search(db,tenant_id=payload.tenant_id,query=payload.query,top_k=payload.top_k)
    if payload.rerank: chunks=rerank(payload.query,chunks,top_k=min(payload.top_k,8))
    return RetrievalResponse(results=chunks)
@router.post("/chat/reviewable")
def reviewable_chat(payload:ReviewableChatRequest,db:Session=Depends(get_db)):
    graph=build_reviewable_graph(db); config={"configurable":{"thread_id":payload.thread_id}}; return graph.invoke({"tenant_id":payload.tenant_id,"question":payload.question},config=config)
@router.post("/chat/reviewable/{thread_id}/resume")
def resume_reviewable_chat(thread_id:str,decision:ReviewDecision,db:Session=Depends(get_db)):
    graph=build_reviewable_graph(db); return resume_review(graph,thread_id=thread_id,decision=decision.model_dump())
@router.post("/chat",response_model=ChatResponse)
def chat(payload:ChatRequest,db:Session=Depends(get_db))->ChatResponse:
    state=build_rag_graph(db).invoke({"tenant_id":payload.tenant_id,"question":payload.question}); return ChatResponse(result=state["answer"])
