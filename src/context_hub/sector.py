from __future__ import annotations

from dataclasses import dataclass, asdict

ALLOWED_MAPPING_STATUS = {
    "VALIDATED_EXACT",
    "VALIDATED_RULE",
    "EMPIRICAL_CANDIDATE",
    "AMBIGUOUS",
    "NO_EQUIVALENCE",
}
STRONG_MAPPING_STATUS = {"VALIDATED_EXACT", "VALIDATED_RULE"}


@dataclass(frozen=True)
class SectorMapping:
    sector_id: str
    uaf_activity_code: str | None
    uaf_activity_name: str
    sii_activity_code: str | None
    sii_activity_name: str | None
    mapping_status: str
    mapping_basis: str
    mapping_confidence: float
    valid_from: str | None = None
    valid_to: str | None = None
    evidence_id: str | None = None
    legal_membership_assertion_allowed: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def sector_mapping(**kwargs) -> dict:
    status = str(kwargs.get("mapping_status") or "").upper()
    if status not in ALLOWED_MAPPING_STATUS:
        raise ValueError(f"mapping_status invalido: {status}")
    kwargs["mapping_status"] = status
    # Ni siquiera una regla fuerte convierte ACTECO en prueba jurídica de inscripción UAF.
    kwargs["legal_membership_assertion_allowed"] = bool(
        kwargs.get("legal_membership_assertion_allowed", False)
    ) and status in STRONG_MAPPING_STATUS
    return SectorMapping(**kwargs).as_dict()


def strong_sector_statement_allowed(mapping: dict, external_membership_evidence: bool = False) -> bool:
    return bool(
        mapping.get("mapping_status") in STRONG_MAPPING_STATUS
        and external_membership_evidence
    )


def classify_legacy_mapping(status: object, confidence: object = None) -> str:
    raw = str(status or "").strip().upper()
    conf = str(confidence or "").strip().upper()
    if raw in ALLOWED_MAPPING_STATUS:
        return raw
    if raw in {"VALIDADO", "VALIDATED", "CODIGO_EXACTO"}:
        return "VALIDATED_RULE"
    if raw in {"EXPERIMENTAL", "CANDIDATO", "SCREENING"}:
        return "EMPIRICAL_CANDIDATE" if conf in {"ALTA", "HIGH"} else "AMBIGUOUS"
    if raw in {"SIN_EQUIVALENCIA", "NO_MATCH", "NONE"}:
        return "NO_EQUIVALENCE"
    return "AMBIGUOUS"
