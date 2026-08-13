import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_no_sermig_in_source_catalog():
    txt=(ROOT/"config/sources.json").read_text(encoding="utf-8").lower()
    assert "sermig" not in txt

def test_sector_mapping_never_asserts_legal_membership():
    rows=[json.loads(x) for x in (ROOT/"data/silver/sector_sii_mapping_v1.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows
    assert all(x["legal_membership_assertion_allowed"] is False for x in rows)

def test_expected_dimension_sizes():
    sectors=(ROOT/"data/silver/dim_sector.jsonl").read_text(encoding="utf-8").splitlines()
    regions=(ROOT/"data/silver/dim_region.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(sectors)==55
    assert len(regions)==16
