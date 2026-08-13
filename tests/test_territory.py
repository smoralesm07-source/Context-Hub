import pytest
from context_hub.territory import canonical_territory_id, alias_lookup, parse_arcgis_features

def test_ids():
    assert canonical_territory_id("REGION","13") == "CL-REG-13"
    assert canonical_territory_id("PROVINCE","131") == "CL-PROV-131"
    assert canonical_territory_id("COMMUNE","13101") == "CL-COM-13101"

def test_invalid_code_rejected():
    with pytest.raises(ValueError):
        canonical_territory_id("COMMUNE","Santiago")

def test_alias_requires_governed_exact_alias():
    rows=[{"alias":"RM","territory_id":"CL-REG-13","status":"ACTIVE"}]
    assert alias_lookup("rm", rows) == "CL-REG-13"
    assert alias_lookup("region metrop", rows) is None

def test_arcgis_exact_codes():
    features=[{"attributes":{"CUT_REG":"13","CUT_PROV":"131","CUT_COM":"13101",
        "REGION":"Metropolitana","PROVINCIA":"Santiago","COMUNA":"Santiago"}}]
    rows=parse_arcgis_features(features)
    assert rows[0]["territory_id"]=="CL-COM-13101"
    assert rows[0]["mapping_method"]=="CODE_EXACT"
