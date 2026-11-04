from uuid import UUID
from pydantic import BaseModel,Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.models import ToolExecution
class CreateTicketInput(BaseModel): subject:str=Field(min_length=3,max_length=200); description:str=Field(min_length=3,max_length=3000); priority:str="normal"
class TicketResult(BaseModel): ticket_id:str; created:bool
def create_support_ticket(db:Session,*,tenant_id:UUID,payload:CreateTicketInput,idempotency_key:str)->TicketResult:
    existing=db.query(ToolExecution).filter(ToolExecution.tenant_id==tenant_id,ToolExecution.idempotency_key==idempotency_key).one_or_none()
    if existing:return TicketResult(**existing.result_json,created=False)
    ticket_id=f"DEMO-{idempotency_key[-8:].upper()}";result={"ticket_id":ticket_id}
    db.add(ToolExecution(tenant_id=tenant_id,tool_name="create_support_ticket",idempotency_key=idempotency_key,request_json=payload.model_dump(),result_json=result))
    try:db.commit()
    except IntegrityError:
        db.rollback();existing=db.query(ToolExecution).filter(ToolExecution.tenant_id==tenant_id,ToolExecution.idempotency_key==idempotency_key).one();return TicketResult(**existing.result_json,created=False)
    return TicketResult(**result,created=True)
