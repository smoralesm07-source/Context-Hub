from __future__ import annotations

from dataclasses import dataclass, asdict

from .ids import commune_id, normalize_text, province_id, region_id


@dataclass(frozen=True)
class Territory:
    territory_id: str
    country_code: str
    territory_level: str
    region_code: str | None
    province_code: str | None
    commune_code: str | None
    canonical_name: str
    source_name: str
    mapping_method: str
    mapping_confidence: float

    def as_dict(self) -> dict:
        return asdict(self)


def build_region(code: object, name: object, source_name: object | None = None) -> dict:
    rid = region_id(code)
    if not rid:
        raise ValueError("region_code requerido")
    canonical = str(name).strip()
    return Territory(
        rid, "CL", "REGION", rid.removeprefix("CL-REG-"), None, None,
        canonical, str(source_name if source_name is not None else name).strip(),
        "CODE_EXACT", 1.0,
    ).as_dict()


def build_province(code: object, name: object, region_code: object) -> dict:
    pid = province_id(code)
    rid = region_id(region_code)
    if not pid or not rid:
        raise ValueError("province_code y region_code requeridos")
    return Territory(
        pid, "CL", "PROVINCE", rid.removeprefix("CL-REG-"), pid.removeprefix("CL-PROV-"), None,
        str(name).strip(), str(name).strip(), "CODE_EXACT", 1.0,
    ).as_dict()


def build_commune(code: object, name: object, region_code: object, province_code: object | None = None) -> dict:
    cid = commune_id(code)
    rid = region_id(region_code)
    pid = province_id(province_code) if province_code is not None else None
    if not cid or not rid:
        raise ValueError("commune_code y region_code requeridos")
    return Territory(
        cid, "CL", "COMMUNE", rid.removeprefix("CL-REG-"),
        pid.removeprefix("CL-PROV-") if pid else None,
        cid.removeprefix("CL-COM-"), str(name).strip(), str(name).strip(), "CODE_EXACT", 1.0,
    ).as_dict()


def alias_record(alias: object, territory_id: str, evidence_id: str | None = None) -> dict:
    return {
        "alias": normalize_text(alias),
        "territory_id": territory_id,
        "mapping_method": "ALIAS_GOVERNED",
        "mapping_confidence": 1.0,
        "evidence_id": evidence_id,
    }
