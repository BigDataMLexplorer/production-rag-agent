def prioritize_current(candidates:list[dict])->list[dict]:return sorted(candidates,key=lambda x:(not x["is_current"],-x["score"]))
def test_current_document_beats_stale_document_even_when_scores_are_close()->None:
    c=[{"version":"2025-01","is_current":False,"score":.91},{"version":"2026-10","is_current":True,"score":.89}];assert prioritize_current(c)[0]["version"]=="2026-10"
