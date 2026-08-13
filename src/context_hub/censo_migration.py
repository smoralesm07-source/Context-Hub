from __future__ import annotations
from pathlib import Path
import re
import pandas as pd
from .territory import canonical_territory_id


def _clean_col(value: object) -> str:
    text = str(value or "").strip().lower()
    text = (text.replace("á","a").replace("é","e").replace("í","i")
                .replace("ó","o").replace("ú","u").replace("ñ","n"))
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _digits(value: object, width: int) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (int, float)):
        try:
            numeric=float(value)
            if numeric.is_integer():
                s=str(int(numeric))
            else:
                s=re.sub(r"\D", "", str(value))
        except Exception:
            s=re.sub(r"\D", "", str(value))
    else:
        text=str(value).strip()
        if re.fullmatch(r"\d+\.0+", text):
            text=text.split(".",1)[0]
        s=re.sub(r"\D", "", text)
    return s.zfill(width) if s else ""


def parse_region_totals(path: str | Path) -> list[dict]:
    df = pd.read_excel(path, sheet_name="1", header=3)
    df.columns = [_clean_col(c) for c in df.columns]
    required = {"codigo_region", "region", "inmigrantes_internacionales"}
    if not required.issubset(df.columns):
        raise ValueError(f"Unexpected Censo sheet 1 columns: {list(df.columns)}")
    out=[]
    for r in df.to_dict("records"):
        code=_digits(r.get("codigo_region"),2)
        if not code or code == "00":
            continue
        count=r.get("inmigrantes_internacionales")
        if pd.isna(count):
            continue
        out.append({
            "territory_id":canonical_territory_id("REGION",code),
            "territory_level":"REGION","region_code":code,
            "region_name":str(r.get("region") or "").strip(),
            "period":2024,"foreign_born_count":int(count),
            "male_foreign_born":None if pd.isna(r.get("hombres")) else int(r.get("hombres")),
            "female_foreign_born":None if pd.isna(r.get("mujeres")) else int(r.get("mujeres")),
            "birthplace_not_declared":None if pd.isna(r.get("lugar_de_nacimiento_no_declarado")) else int(r.get("lugar_de_nacimiento_no_declarado")),
            "source_id":"INE_CENSO2024_INMIGRACION","source_tier":"PRIMARY_OFFICIAL",
            "context_only":True,"aml_interpretation":"NONE","schema_version":"1.0",
        })
    if len(out) != 16:
        raise ValueError(f"Expected 16 regional rows, got {len(out)}")
    return sorted(out,key=lambda x:x["region_code"])


def parse_commune_totals(path: str | Path) -> list[dict]:
    df = pd.read_excel(path, sheet_name="4", header=3)
    df.columns = [_clean_col(c) for c in df.columns]
    required={"codigo_region","region","codigo_provincia","provincia","codigo_comuna","comuna","pais_o_continente_de_nacimiento","inmigrantes_internacionales"}
    if not required.issubset(df.columns):
        raise ValueError(f"Unexpected Censo sheet 4 columns: {list(df.columns)}")
    out=[]
    for r in df.to_dict("records"):
        label=_clean_col(r.get("pais_o_continente_de_nacimiento"))
        if label != "total_nacidos_fuera_del_pais":
            continue
        reg=_digits(r.get("codigo_region"),2); prov=_digits(r.get("codigo_provincia"),3); com=_digits(r.get("codigo_comuna"),5)
        if not com or com == "00000":
            continue
        count=r.get("inmigrantes_internacionales")
        if pd.isna(count):
            continue
        out.append({
            "territory_id":canonical_territory_id("COMMUNE",com),
            "territory_level":"COMMUNE","region_code":reg,"province_code":prov,"commune_code":com,
            "region_id":canonical_territory_id("REGION",reg),"province_id":canonical_territory_id("PROVINCE",prov),
            "region_name":str(r.get("region") or "").strip(),"province_name":str(r.get("provincia") or "").strip(),"commune_name":str(r.get("comuna") or "").strip(),
            "period":2024,"foreign_born_count":int(count),
            "source_id":"INE_CENSO2024_INMIGRACION","source_tier":"PRIMARY_OFFICIAL",
            "context_only":True,"aml_interpretation":"NONE","schema_version":"1.0",
        })
    if len(out) < 340:
        raise ValueError(f"Unexpected commune coverage in Censo workbook: {len(out)}")
    return sorted(out,key=lambda x:x["commune_code"])


def territory_rows_from_commune_totals(rows: list[dict]) -> list[dict]:
    return [{
        "territory_id":r["territory_id"],"country_code":"CL","territory_level":"COMMUNE",
        "region_code":r["region_code"],"province_code":r["province_code"],"commune_code":r["commune_code"],
        "region_id":r["region_id"],"province_id":r["province_id"],
        "canonical_name":r["commune_name"],"province_name":r["province_name"],"region_name":r["region_name"],
        "source_system":"INE_CENSO2024_INMIGRACION","mapping_method":"CODE_EXACT","mapping_confidence":1.0,"schema_version":"1.0",
    } for r in rows]
