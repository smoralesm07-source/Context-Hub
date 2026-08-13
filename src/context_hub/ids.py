from __future__ import annotations

import re
import unicodedata


def normalize_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^A-Za-z0-9]+", " ", text.upper()).strip()
    return re.sub(r"\s+", " ", text)


def normalize_rut(value: object) -> str | None:
    raw = re.sub(r"[^0-9Kk]", "", "" if value is None else str(value)).upper()
    if len(raw) < 2 or not raw[:-1].isdigit():
        return None
    body = raw[:-1].lstrip("0") or "0"
    return f"{body}-{raw[-1]}"


def rut_is_valid(value: object) -> bool:
    rut = normalize_rut(value)
    if not rut:
        return False
    body, dv = rut.split("-")
    total = 0
    multiplier = 2
    for digit in reversed(body):
        total += int(digit) * multiplier
        multiplier = 2 if multiplier == 7 else multiplier + 1
    remainder = 11 - total % 11
    expected = "0" if remainder == 11 else "K" if remainder == 10 else str(remainder)
    return dv == expected


def entity_id_from_rut(value: object) -> str | None:
    rut = normalize_rut(value)
    return f"ENT-RUT-{rut}" if rut and rut_is_valid(rut) else None


def region_id(code: object) -> str | None:
    digits = re.sub(r"\D", "", "" if code is None else str(code))
    return f"CL-REG-{digits.zfill(2)}" if digits else None


def province_id(code: object) -> str | None:
    digits = re.sub(r"\D", "", "" if code is None else str(code))
    return f"CL-PROV-{digits.zfill(3)}" if digits else None


def commune_id(code: object) -> str | None:
    digits = re.sub(r"\D", "", "" if code is None else str(code))
    return f"CL-COM-{digits.zfill(5)}" if digits else None
