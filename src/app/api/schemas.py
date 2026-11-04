from uuid import UUID
from pydantic import BaseModel,Field
from app.retrieval.schemas import Answer,RetrievedChunk
class ChatRequest(BaseModel): tenant_id:UUID; question:str=Field(min_length=3,max_length=4000)
class ChatResponse(BaseModel): result:Answer
class RetrievalRequest(BaseModel): tenant_id:UUID; query:str=Field(min_length=2,max_length=4000); top_k:int=Field(default=8,ge=1,le=50); rerank:bool=True
class RetrievalResponse(BaseModel): results:list[RetrievedChunk]
class IngestionResponse(BaseModel): document_version_id:UUID; version:str; is_current:bool
class ReviewableChatRequest(BaseModel): tenant_id:UUID; question:str=Field(min_length=3,max_length=4000); thread_id:str=Field(min_length=3,max_length=200)
class ReviewDecision(BaseModel): approved:bool; edited_answer:str|None=None
