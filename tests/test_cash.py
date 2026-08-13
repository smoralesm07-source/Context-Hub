import pytest
from context_hub.cash import cash_exposure, validate_geography, add_cash_trend, sector_cash_exposure

def test_cash_dynamic_coverage():
    x=cash_exposure({"cash_usage_rate":70})
    assert x["cash_exposure_index_v1"]==70
    assert x["score_coverage"]==0.35
    assert x["aml_interpretation"]=="NONE"

def test_no_downscaling():
    with pytest.raises(ValueError):
        validate_geography({"source_representativeness":"MACROZONE","territory_level":"COMMUNE"})

def test_same_grain_ok():
    validate_geography({"source_representativeness":"MACROZONE","territory_level":"MACROZONE"})

def test_sector_cash_requires_source_support():
    with pytest.raises(ValueError):
        sector_cash_exposure({"sector_id":"UAF-SEC-14","cash_usage_rate":80})
    out=sector_cash_exposure({"sector_id":"UAF-SEC-14","cash_usage_rate":80,"source_supports_sector_grain":True})
    assert out["cash_exposure_index_v1"]==80

def test_cash_trend():
    rows=[
      {"territory_id":"T","sector_id":None,"period":"2024","cash_usage_rate":50},
      {"territory_id":"T","sector_id":None,"period":"2025","cash_usage_rate":60}
    ]
    out=add_cash_trend(rows)
    assert out[1]["cash_exposure_delta_prev"]==10
