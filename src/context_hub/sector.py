from __future__ import annotations

STRONG_MEMBERSHIP = {"VALIDATED_EXACT", "VALIDATED_RULE"}

def sector_id(value: int | str) -> str:
    n = int(value)
    if not 1 <= n <= 55:
        raise ValueError("UAF sector id must be 1..55")
    return f"UAF-SEC-{n:02d}"

def can_assert_membership(mapping: dict, external_validation_satisfied: bool = False) -> bool:
    """ACTECO alone never proves UAF status. VALIDATED_RULE needs its external condition."""
    status = mapping.get("mapping_status")
    if status == "VALIDATED_EXACT":
        return bool(mapping.get("legal_membership_assertion_allowed"))
    if status == "VALIDATED_RULE":
        return bool(mapping.get("legal_membership_assertion_allowed")) and external_validation_satisfied
    return False

def mapping_use(mapping: dict) -> str:
    status = mapping.get("mapping_status")
    if status in STRONG_MEMBERSHIP:
        return "GOVERNED_RULE"
    if status == "EMPIRICAL_CANDIDATE":
        return "SCREENING"
    if status == "AMBIGUOUS":
        return "PRESELECTION_ONLY"
    return "NO_DIRECT_MAPPING"
