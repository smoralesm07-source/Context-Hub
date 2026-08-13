from __future__ import annotations

from .scoring import weighted_score

MIGRATION_WEIGHTS = {
    "immigrant_population_share": 0.50,
    "international_movement_intensity": 0.35,
    "comparable_migration_change": 0.15,
}


def migration_exposure_index(
    immigrant_population_share: float | None = None,
    international_movement_intensity: float | None = None,
    comparable_migration_change: float | None = None,
) -> dict:
    result = weighted_score(
        {
            "immigrant_population_share": immigrant_population_share,
            "international_movement_intensity": international_movement_intensity,
            "comparable_migration_change": comparable_migration_change,
        },
        MIGRATION_WEIGHTS,
    )
    return {
        "index_name": "migration_exposure_index_v1",
        "score": result["score"],
        "coverage": result["coverage"],
        "components_used": result["components_used"],
        "context_only": True,
        "aml_interpretation": "NONE",
        "nationality_as_aml_proxy": False,
        "cross_grain_downscaling_allowed": False,
    }


def migration_fact(territory_id: str, period_id: str, **metrics) -> dict:
    return {
        "interop_version": "1.0",
        "record_type": "MIGRATION_CONTEXT",
        "territory_id": territory_id,
        "period_id": period_id,
        **metrics,
        "context_only": True,
        "aml_interpretation": "NONE",
        "nationality_as_aml_proxy": False,
    }
