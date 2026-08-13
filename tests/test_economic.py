from context_hub.economic import percentile_rank, enrich_peer_context, join_macro_context

def test_percentile():
    assert percentile_rank(3,[1,2,3,4,5]) == 50.0

def test_macro_join_exact_codes():
    entities=[{"entity_id":"E","year":2024,"activity_code":"A","region_code":"13"}]
    macro=[{"year":2024,"activity_code":"A","region_code":"13","sector_growth_yoy":2.5}]
    out=join_macro_context(entities,macro)[0]
    assert out["sector_growth_yoy"]==2.5
    assert out["macro_context_level"]=="ACTIVITY_REGION_YEAR"

def test_peer_fallback_and_context():
    rows=[]
    for i in range(25):
        rows.append({"entity_id":f"E{i}","year":2024,"activity_code":"A","region_code":"13",
            "commune_code":"13101","sales_band_rank":i%10,"workers":i+1,"start_year":2020})
    out=enrich_peer_context(rows,min_peer_count=20)
    assert out[0]["peer_group_level"]=="ACTIVITY_COMMUNE_YEAR"
    assert out[0]["peer_group_sufficient"] is True
    assert out[0]["sales_measure"]=="SII_SALES_BAND"
    assert out[0]["aml_interpretation"]=="NONE"

def test_small_group_is_explicitly_insufficient():
    rows=[{"entity_id":"E1","year":2024,"activity_code":"A","region_code":"13",
        "commune_code":"13101","sales_band_rank":1,"workers":1,"start_year":2024}]
    out=enrich_peer_context(rows,min_peer_count=20)[0]
    assert out["peer_group_sufficient"] is False
