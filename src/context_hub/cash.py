from __future__ import annotations

from .scoring import weighted_score

CASH_WEIGHTS = {
    "cash_usage_rate": 0.35,
    "cash_frequency": 0.30,
    "cash_value_share": 0.20,
    "cash_preference": 0.15,
}


def cash_exposure_index(
    cash_usage_rate: float | None = None,
    cash_frequency: float | None = None,
    cash_value_share: float | None = None,
    cash_preference: float | None = None,
) -> dict:
    result = weighted_score(
        {
            "cash_usage_rate": cash_usage_rate,
            "cash_frequency": cash_frequency,
            "cash_value_share": cash_value_share,
            "cash_preference": cash_preference,
        },
        CASH_WEIGHTS,
    )
    return {
        "index_name": "cash_exposure_index_v1",
        "score": result["score"],
        "coverage": result["coverage"],
        "components_used": result["components_used"],
        "context_only": True,
        "aml_interpretation": "NONE",
        "cross_grain_downscaling_allowed": False,
    }


def cash_trend(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return round(float(current) - float(previous), 2)


def cash_fact(geography_level: str, geography_id: str, period_id: str, **metrics) -> dict:
    allowed = {"COUNTRY", "MACROZONE", "REGION", "COMMUNE", "SECTOR"}
    if geography_level not in allowed:
        raise ValueError(f"geography_level invalido: {geography_level}")
    return {
        "interop_version": "1.0",
        "record_type": "CASH_CONTEXT",
        "geography_level": geography_level,
        "geography_id": geography_id,
        "period_id": period_id,
        **metrics,
        "context_only": True,
        "aml_interpretation": "NONE",
    }
