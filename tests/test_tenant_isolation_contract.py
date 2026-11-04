from uuid import uuid4
def tenant_filter(rows:list[dict],tenant_id):return [r for r in rows if r["tenant_id"]==tenant_id]
def test_tenant_isolation_contract()->None:
    a=uuid4();n=uuid4();rows=[{"tenant_id":a,"content":"Acme secret policy"},{"tenant_id":n,"content":"Northstar secret policy"}];assert [r["content"] for r in tenant_filter(rows,a)]==["Acme secret policy"]
