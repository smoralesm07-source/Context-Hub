from __future__ import annotations
from typing import Mapping

def weighted_available_score(
    values: Mapping[str, float | int | None],
    weights: Mapping[str, float],
) -> dict:
    """Score 0-100, renormalizing over available components. Missing is never zero."""
    numerator = 0.0
    available_weight = 0.0
    total_weight = sum(float(v) for v in weights.values())
    used = {}
    for key, weight in weights.items():
        value = values.get(key)
        if value is None:
            continue
        value = float(value)
        if not 0 <= value <= 100:
            raise ValueError(f"{key} must be in [0,100], got {value}")
        w = float(weight)
        numerator += value * w
        available_weight += w
        used[key] = value
    if not available_weight:
        return {"score": None, "coverage": 0.0, "components_used": {}}
    return {
        "score": round(numerator / available_weight, 2),
        "coverage": round(available_weight / total_weight, 4) if total_weight else 0.0,
        "components_used": used,
    }

def freshness_state(days_since_success: int | None, stale_after_days: int) -> str:
    if days_since_success is None:
        return "UNKNOWN"
    if days_since_success <= stale_after_days:
        return "CURRENT"
    if days_since_success <= int(stale_after_days * 1.5):
        return "DUE"
    return "STALE"
