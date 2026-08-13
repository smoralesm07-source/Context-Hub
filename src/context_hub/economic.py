from __future__ import annotations

from collections import defaultdict

from .scoring import percentile_rank, weighted_score

MIN_PEERS_DEFAULT = 20


def _key(row: dict, level: str) -> tuple:
    activity = str(row.get("sii_activity_code") or "").strip()
    year = str(row.get("period_id") or row.get("year") or "").strip()
    if level == "COMMUNE":
        return activity, str(row.get("commune_id") or ""), year
    if level == "REGION":
        return activity, str(row.get("region_id") or ""), year
    return activity, "CL", year


def peer_group(target: dict, universe: list[dict], min_peers: int = MIN_PEERS_DEFAULT) -> dict:
    """Selecciona ACTECO×comuna×periodo, luego región y finalmente Chile.

    El target puede permanecer dentro del grupo: percentiles se interpretan como
    posición en la población observable, no como estimación causal.
    """
    for level in ("COMMUNE", "REGION", "COUNTRY"):
        target_key = _key(target, level)
        if not target_key[0] or not target_key[-1]:
            continue
        rows = [row for row in universe if _key(row, level) == target_key]
        if len(rows) >= min_peers or level == "COUNTRY":
            return {"peer_level": level, "peer_key": target_key, "peer_count": len(rows), "rows": rows}
    return {"peer_level": None, "peer_key": None, "peer_count": 0, "rows": []}


def benchmark_entity(target: dict, universe: list[dict], min_peers: int = MIN_PEERS_DEFAULT) -> dict:
    peers = peer_group(target, universe, min_peers=min_peers)
    rows = peers["rows"]
    sales = [row.get("sales_band_rank") for row in rows if row.get("sales_band_rank") is not None]
    workers = [row.get("workers") for row in rows if row.get("workers") is not None]
    ages = [row.get("company_age_years") for row in rows if row.get("company_age_years") is not None]

    sales_p = percentile_rank(target.get("sales_band_rank"), sales)
    workers_p = percentile_rank(target.get("workers"), workers)
    age_p = percentile_rank(target.get("company_age_years"), ages)
    gap = None if sales_p is None or workers_p is None else round(sales_p - workers_p, 2)

    return {
        "record_type": "ECONOMIC_PEER_BENCHMARK",
        "entity_id": target.get("entity_id"),
        "sii_activity_code": target.get("sii_activity_code"),
        "period_id": target.get("period_id") or target.get("year"),
        "territory_id": target.get("commune_id") or target.get("region_id"),
        "peer_level": peers["peer_level"],
        "peer_count": peers["peer_count"],
        "sales_band_percentile": sales_p,
        "workers_percentile": workers_p,
        "company_age_percentile": age_p,
        "sales_worker_gap": gap,
        "company_sales_band_delta_1y": target.get("company_sales_band_delta_1y"),
        "exact_sales_inferred": False,
        "context_only": True,
        "aml_interpretation": "NONE",
    }


def economic_divergence_index(
    sales_percentile: float | None,
    workers_percentile: float | None,
    company_growth_percentile: float | None = None,
    sector_growth_percentile: float | None = None,
) -> dict:
    sales_worker_gap = None
    if sales_percentile is not None and workers_percentile is not None:
        sales_worker_gap = min(100.0, abs(float(sales_percentile) - float(workers_percentile)))

    growth_divergence = None
    if company_growth_percentile is not None and sector_growth_percentile is not None:
        growth_divergence = min(100.0, abs(float(company_growth_percentile) - float(sector_growth_percentile)))

    result = weighted_score(
        {"sales_worker_gap": sales_worker_gap, "growth_divergence": growth_divergence},
        {"sales_worker_gap": 0.60, "growth_divergence": 0.40},
    )
    return {
        "index_name": "economic_divergence_index_v1",
        "score": result["score"],
        "coverage": result["coverage"],
        "components_used": result["components_used"],
        "context_only": True,
        "aml_interpretation": "NONE",
    }


def attach_macro_context(benchmark: dict, macro_rows: list[dict]) -> dict:
    """Une sólo por claves explícitas compatibles; no hace fuzzy joins."""
    activity = str(benchmark.get("sii_activity_code") or "")
    period = str(benchmark.get("period_id") or "")
    territory = str(benchmark.get("territory_id") or "")
    candidates = [
        row for row in macro_rows
        if str(row.get("period_id") or "") == period
        and (not row.get("sii_activity_code") or str(row.get("sii_activity_code")) == activity)
        and (not row.get("territory_id") or str(row.get("territory_id")) == territory)
    ]
    out = dict(benchmark)
    out["macro_context"] = candidates
    out["macro_context_count"] = len(candidates)
    return out
