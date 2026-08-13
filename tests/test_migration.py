from context_hub.migration import migration_exposure, exposure_label

def test_missing_component_is_not_zero():
    x=migration_exposure({"foreign_resident_share_percentile":80})
    assert x["migration_exposure_index_v1"] == 80
    assert x["score_coverage"] == 0.5

def test_context_not_aml():
    x=migration_exposure({"foreign_resident_share_percentile":50})
    assert x["context_only"] is True
    assert x["aml_interpretation"] == "NONE"
    assert x["nationality_as_aml_proxy"] is False

def test_label_requires_coverage():
    assert exposure_label(90,0.35) == "INSUFFICIENT_COVERAGE"
