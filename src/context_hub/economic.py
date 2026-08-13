from __future__ import annotations
from collections import defaultdict
from statistics import median

def percentile_rank(value: float | int | None, sample: list[float | int]) -> float | None:
    if value is None or not sample:
        return None
    xs = sorted(float(x) for x in sample if x is not None)
    if not xs: return None
    v=float(value)
    less=sum(x<v for x in xs); equal=sum(x==v for x in xs)
    return round(100.0*(less+0.5*equal)/len(xs),2)

def company_age_years(start_year: int | None, year: int) -> int | None:
    return None if start_year is None else max(0,int(year)-int(start_year))

def _key(row: dict, fields: tuple[str,...]):
    return tuple(row.get(f) for f in fields)

def join_macro_context(entity_rows: list[dict], macro_rows: list[dict]) -> list[dict]:
    """Attach aggregate context without changing entity facts.

    Macro rows may be at activity×region×year or activity×year. The most specific
    exact-code match wins. Names are never join keys.
    """
    region_idx={}
    national_idx={}
    for m in macro_rows:
        act=m.get("activity_code"); year=m.get("year")
        reg=m.get("region_code")
        if reg:
            region_idx[(act,reg,year)]=m
        else:
            national_idx[(act,year)]=m
    out=[]
    for r in entity_rows:
        m=region_idx.get((r.get("activity_code"),r.get("region_code"),r.get("year")))
        level="ACTIVITY_REGION_YEAR"
        if m is None:
            m=national_idx.get((r.get("activity_code"),r.get("year")))
            level="ACTIVITY_NATIONAL_YEAR" if m else None
        merged=dict(r)
        if m:
            for field in (
                "sector_growth_yoy","region_sector_gdp_growth_yoy","credit_growth_yoy",
                "informality_rate","n_companies_context","macro_source_ids"
            ):
                if field in m:
                    merged[field]=m[field]
        merged["macro_context_level"]=level
        out.append(merged)
    return out

def enrich_peer_context(rows: list[dict], min_peer_count: int=20) -> list[dict]:
    """Peer comparisons without pretending that SII sales bands are exact revenues."""
    hierarchy=[
        ("ACTIVITY_COMMUNE_YEAR",("activity_code","commune_code","year")),
        ("ACTIVITY_REGION_YEAR",("activity_code","region_code","year")),
        ("ACTIVITY_NATIONAL_YEAR",("activity_code","year")),
    ]
    groups={name:defaultdict(list) for name,_ in hierarchy}
    for row in rows:
        for name,fields in hierarchy:
            groups[name][_key(row,fields)].append(row)

    out=[]
    for row in rows:
        chosen_name,peers=None,[]
        for name,fields in hierarchy:
            candidate=groups[name][_key(row,fields)]
            if len(candidate)>=min_peer_count:
                chosen_name,peers=name,candidate; break
        if not peers:
            name,fields=hierarchy[-1]
            chosen_name,peers=name,groups[name][_key(row,fields)]

        sales=[p.get("sales_band_rank") for p in peers if p.get("sales_band_rank") is not None]
        workers=[p.get("workers") for p in peers if p.get("workers") is not None]
        ages=[company_age_years(p.get("start_year"),int(p.get("year"))) for p in peers]
        ages=[x for x in ages if x is not None]
        sp=percentile_rank(row.get("sales_band_rank"),sales)
        wp=percentile_rank(row.get("workers"),workers)
        age=company_age_years(row.get("start_year"),int(row.get("year")))
        ap=percentile_rank(age,ages)
        gap=round(sp-wp,2) if sp is not None and wp is not None else None

        components={}
        if gap is not None: components["sales_worker_gap"]=min(100.0,abs(gap))
        delta=row.get("company_sales_band_delta_1y")
        if delta is not None: components["sales_band_change"]=min(100.0,abs(float(delta))*20.0)
        sector_growth=row.get("sector_growth_yoy")
        company_growth_proxy=row.get("company_growth_proxy")
        if sector_growth is not None and company_growth_proxy is not None:
            components["company_vs_sector_growth"]=min(100.0,abs(float(company_growth_proxy)-float(sector_growth)))
        divergence=round(sum(components.values())/len(components),2) if components else None

        out.append({
            **row,
            "peer_group_level":chosen_name,"peer_group_n":len(peers),
            "peer_group_sufficient":len(peers)>=min_peer_count,
            "sales_measure":"SII_SALES_BAND",
            "sales_band_percentile":sp,"workers_percentile":wp,
            "company_age_years":age,"company_age_percentile":ap,
            "sales_worker_gap":gap,
            "peer_sales_band_median":median(sales) if sales else None,
            "peer_workers_median":median(workers) if workers else None,
            "economic_divergence_index_v1":divergence,
            "divergence_components":components,
            "context_only":True,"aml_interpretation":"NONE",
        })
    return out
