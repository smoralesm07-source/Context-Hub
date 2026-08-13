from context_hub.quality import weighted_available_score, freshness_state

def test_missing_not_zero():
    x=weighted_available_score({"a":100,"b":None},{"a":0.5,"b":0.5})
    assert x["score"] == 100
    assert x["coverage"] == 0.5

def test_freshness():
    assert freshness_state(None,30) == "UNKNOWN"
    assert freshness_state(10,30) == "CURRENT"
    assert freshness_state(40,30) == "DUE"
    assert freshness_state(60,30) == "STALE"
