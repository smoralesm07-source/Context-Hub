from __future__ import annotations
import re
import unicodedata
from pathlib import Path
from typing import Iterable
import pandas as pd

LEVEL_PREFIX = {"REGION": "REG", "PROVINCE": "PROV", "COMMUNE": "COM"}

def canonical_territory_id(level: str, code: object) -> str:
    level = str(level).upper()
    if level not in LEVEL_PREFIX:
        raise ValueError(f"Unsupported territory level: {level}")
    digits = re.sub(r"\D", "", str(code or ""))
    expected = {"REGION": 2, "PROVINCE": 3, "COMMUNE": 5}[level]
    if len(digits) != expected:
        raise ValueError(f"{level} code must have {expected} digits: {code}")
    return f"CL-{LEVEL_PREFIX[level]}-{digits}"

def normalize_name(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").upper()
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()

def alias_lookup(alias: str, alias_rows: Iterable[dict]) -> str | None:
    key = normalize_name(alias)
    matches = [r["territory_id"] for r in alias_rows if normalize_name(r.get("alias")) == key and r.get("status") == "ACTIVE"]
    return matches[0] if len(set(matches)) == 1 else None

def _clean_col(c: object) -> str:
    return normalize_name(c).replace(" ", "_")

def _build_commune_row(r: dict, source_system: str) -> dict:
    reg = re.sub(r"\D","",str(r["CUT_REG"])).zfill(2)
    prov = re.sub(r"\D","",str(r["CUT_PROV"])).zfill(3)
    com = re.sub(r"\D","",str(r["CUT_COM"])).zfill(5)
    return {
        "territory_id": canonical_territory_id("COMMUNE", com),
        "country_code":"CL","territory_level":"COMMUNE",
        "region_code":reg,"province_code":prov,"commune_code":com,
        "region_id":canonical_territory_id("REGION", reg),
        "province_id":canonical_territory_id("PROVINCE", prov),
        "canonical_name":str(r["COMUNA"]).strip(),
        "province_name":str(r["PROVINCIA"]).strip(),
        "region_name":str(r["REGION"]).strip(),
        "source_system":source_system,
        "mapping_method":"CODE_EXACT","mapping_confidence":1.0,"schema_version":"1.0",
    }

def _validate_rows(rows: list[dict]) -> list[dict]:
    ids = [r["territory_id"] for r in rows]
    if not rows:
        raise ValueError("Territory source returned zero communes")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate commune CUTs in source")
    return sorted(rows, key=lambda x: x["commune_code"])

def parse_subdere_cut_xls(path: str | Path) -> list[dict]:
    """Parse official SUBDERE CUT XLS; only exact codes create canonical IDs."""
    df = pd.read_excel(path, engine="xlrd")
    df.columns = [_clean_col(c) for c in df.columns]
    aliases = {
        "CODIGO_REGION_2018":"CUT_REG","CODIGO_REGION":"CUT_REG","CUT_REG":"CUT_REG",
        "CODIGO_PROVINCIA_2018":"CUT_PROV","CODIGO_PROVINCIA":"CUT_PROV","CUT_PROV":"CUT_PROV",
        "CODIGO_COMUNA_2018":"CUT_COM","CODIGO_COMUNA":"CUT_COM","CUT_COM":"CUT_COM",
        "REGION":"REGION","NOMBRE_REGION":"REGION",
        "PROVINCIA":"PROVINCIA","NOMBRE_PROVINCIA":"PROVINCIA",
        "COMUNA":"COMUNA","NOMBRE_COMUNA":"COMUNA",
    }
    df = df.rename(columns={c: aliases.get(c, c) for c in df.columns})
    required = {"CUT_REG","CUT_PROV","CUT_COM","REGION","PROVINCIA","COMUNA"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CUT columns not found: {sorted(missing)}; got {list(df.columns)}")
    rows = [_build_commune_row(r,"SUBDERE_CUT") for r in df.to_dict("records")]
    return _validate_rows(rows)

def parse_arcgis_features(features: list[dict], source_system: str = "IDE_CHILE_DPA_2023") -> list[dict]:
    rows=[]
    for feature in features:
        attrs=feature.get("attributes", feature)
        required={"CUT_REG","CUT_PROV","CUT_COM","REGION","PROVINCIA","COMUNA"}
        if not required.issubset(attrs):
            continue
        rows.append(_build_commune_row(attrs, source_system))
    return _validate_rows(rows)
