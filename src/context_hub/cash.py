from __future__ import annotations
from collections import defaultdict
from .quality import weighted_available_score

DEFAULT_WEIGHTS={
    "cash_usage_rate":0.35,
    "cash_transaction_frequency":0.30,
    "cash_value_share":0.20,
    "cash_preference_rate":0.15,
}

def cash_exposure(record: dict, weights: dict|None=None) -> dict:
    weights=weights or DEFAULT_WEIGHTS
    values={k:record.get(k) for k in weights}
    result=weighted_available_score(values,weights)
    return {
        **record,
        "cash_exposure_index_v1":result["score"],
        "score_coverage":result["coverage"],
        "score_components":result["components_used"],
        "context_only":True,"aml_interpretation":"NONE",
    }

def validate_geography(record: dict) -> None:
    source_level=str(record.get("source_representativeness") or "").upper()
    output_level=str(record.get("territory_level") or "").upper()
    rank={"NATIONAL":0,"MACROZONE":1,"REGION":2,"COMMUNE":3}
    if source_level in rank and output_level in rank and rank[output_level]>rank[source_level]:
        raise ValueError("Cannot downscale cash survey below source representativeness")

def add_cash_trend(rows: list[dict], key_fields: tuple[str,...]=("territory_id","sector_id")) -> list[dict]:
    """Add period-over-period change only within the same comparable series."""
    grouped=defaultdict(list)
    for r in rows:
        grouped[tuple(r.get(k) for k in key_fields)].append(r)
    out=[]
    for _,group in grouped.items():
        group=sorted(group,key=lambda x:str(x.get("period") or ""))
        prev=None
        for row in group:
            enriched=cash_exposure(row)
            score=enriched["cash_exposure_index_v1"]
            enriched["cash_exposure_delta_prev"]=round(score-prev,2) if score is not None and prev is not None else None
            if score is not None: prev=score
            out.append(enriched)
    return out

def sector_cash_exposure(record: dict) -> dict:
    if not record.get("sector_id"):
        raise ValueError("sector_id is required for sector cash exposure")
    # Only accept sector/category evidence explicitly supported by the source.
    if not record.get("source_supports_sector_grain", False):
        raise ValueError("Source does not support sector-level cash exposure")
    return cash_exposure(record)
