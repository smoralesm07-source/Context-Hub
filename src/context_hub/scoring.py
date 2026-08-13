from __future__ import annotations

from math import isfinite
from statistics import median


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def weighted_score(components: dict[str, float | None], weights: dict[str, float]) -> dict:
    """Promedia sólo componentes observados y reporta cobertura.

    Un faltante nunca se convierte en cero. La cobertura corresponde a la suma
    de pesos originalmente disponible.
    """
    total_weight = sum(max(0.0, float(w)) for w in weights.values())
    observed = []
    observed_weight = 0.0
    for key, weight in weights.items():
        value = components.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if not isfinite(numeric):
            continue
        w = max(0.0, float(weight))
        observed.append((key, clamp(numeric), w))
        observed_weight += w
    if not observed or observed_weight <= 0:
        return {"score": None, "coverage": 0.0, "components_used": []}
    score = sum(value * weight for _, value, weight in observed) / observed_weight
    coverage = 100.0 * observed_weight / total_weight if total_weight else 100.0
    return {
        "score": round(clamp(score), 2),
        "coverage": round(clamp(coverage), 2),
        "components_used": [key for key, _, _ in observed],
    }


def percentile_rank(value: float | int | None, population: list[float | int]) -> float | None:
    vals = sorted(float(x) for x in population if x is not None)
    if value is None or not vals:
        return None
    v = float(value)
    below = sum(x < v for x in vals)
    equal = sum(x == v for x in vals)
    return round(100.0 * (below + 0.5 * equal) / len(vals), 2)


def robust_center(values: list[float | int]) -> float | None:
    vals = [float(x) for x in values if x is not None]
    return median(vals) if vals else None
