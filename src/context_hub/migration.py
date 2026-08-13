from __future__ import annotations
from .quality import weighted_available_score

DEFAULT_WEIGHTS = {
    "foreign_resident_share_percentile": 0.50,
    "international_passenger_intensity_percentile": 0.35,
    "migration_change_percentile": 0.15,
}

def migration_exposure(record: dict, weights: dict | None = None) -> dict:
    """Territorial exposure index. It is explicitly not an AML score."""
    weights = weights or DEFAULT_WEIGHTS
    values = {k: record.get(k) for k in weights}
    result = weighted_available_score(values, weights)
    return {
        **record,
        "migration_exposure_index_v1": result["score"],
        "score_coverage": result["coverage"],
        "score_components": result["components_used"],
        "context_only": True,
        "aml_interpretation": "NONE",
        "nationality_as_aml_proxy": False,
    }

def exposure_label(score: float | None, coverage: float, minimum_coverage: float = 0.50) -> str:
    if score is None or coverage < minimum_coverage:
        return "INSUFFICIENT_COVERAGE"
    if score >= 80: return "VERY_HIGH"
    if score >= 60: return "HIGH"
    if score >= 40: return "MEDIUM"
    if score >= 20: return "LOW"
    return "VERY_LOW"
