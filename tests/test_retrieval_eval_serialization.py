from app.evaluation.retrieval_eval import CaseResult,ModeSummary,serialize_results
def test_serialize_evaluation_results()->None:
    c=CaseResult(mode="hybrid",tenant="acme",question="q",expected_document_external_id="doc",expected_version="v2",top_document_external_id="doc",top_version="v2",hit_at_1=1.0,hit_at_3=1.0,mrr=1.0,current_version_correct=1.0,tenant_leakage_count=0,latency_ms=10.0);s=ModeSummary(mode="hybrid",cases=1,hit_at_1=1.0,hit_at_3=1.0,mrr=1.0,current_version_accuracy=1.0,tenant_leakage_count=0,mean_latency_ms=10.0);assert serialize_results([c],[s])["summary"][0]["mrr"]==1.0
