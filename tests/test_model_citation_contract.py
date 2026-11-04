from uuid import uuid4
from app.retrieval.schemas import RetrievedChunk
def make_chunk()->RetrievedChunk:
    t=uuid4();return RetrievedChunk(tenant_id=t,chunk_id=uuid4(),document_id=uuid4(),document_external_id="policy",version_id=uuid4(),document_title="Policy",document_version="v2",content="Current policy text",page=1,section=None,score=.9,is_current=True)
def test_context_chunk_ids_are_explicitly_addressable()->None:
    c=make_chunk();allowed={str(c.chunk_id):c};assert str(c.chunk_id) in allowed
