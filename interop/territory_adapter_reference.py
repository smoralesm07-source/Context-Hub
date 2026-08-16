"""Adaptador de referencia para resolver territorio en un radar.

Copiar este archivo dentro del radar y vendorizar junto a él el índice
`data/gold/territory_resolution_index_v1.json` publicado por Context Hub.
El radar no necesita importar `context_hub`: sólo estas ~70 líneas y el JSON.

Uso típico en el exportador de fusión del radar:

    from .territory import resolve

    territory_id, status = resolve(row["comuna"], "COMMUNE")
    record["territory_id"] = territory_id
    record["territory_mapping_status"] = status

Reglas que el adaptador hereda y no puede relajar:

- Sólo igualdad exacta sobre la clave normalizada; nunca similitud.
- El nivel es obligatorio. Siete topónimos son a la vez región y comuna, y
  «Los Lagos» es una comuna de la Región de Los Ríos: resolver sin declarar el
  nivel asigna el dato a la región equivocada.
- Lo no resuelto se marca con un estado explícito y se reporta como brecha.

Referencia implementada y verificada en `Radar-CGR/radar_cgr/territory.py`.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

# Ajustar a la ubicación del índice vendorizado dentro del radar.
INDEX_PATH = Path(__file__).resolve().parents[1] / "config" / "territory_resolution_index_v1.json"

_PREFIXES = (
    "REGION DE LA", "REGION DEL", "REGION DE", "REGION",
    "PROVINCIA DE LA", "PROVINCIA DEL", "PROVINCIA DE", "PROVINCIA",
    "COMUNA DE LA", "COMUNA DEL", "COMUNA DE", "COMUNA",
    "DE LA", "DEL", "DE",
)


def match_key(value: object) -> str:
    """Receta de clave del ecosistema. Debe coincidir bit a bit con el hub."""
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text).strip()
    for prefix in _PREFIXES:
        if text == prefix:
            return ""
        if text.startswith(prefix + " "):
            text = text[len(prefix) + 1:].strip()
            break
    return text.replace(" ", "")


@lru_cache(maxsize=1)
def _index() -> dict:
    if not INDEX_PATH.exists():
        return {"index": {}, "max_key_len": 45}
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def resolve(text: object, level: str) -> tuple[str | None, str]:
    """Devuelve `(territory_id, mapping_status)`. `level` es REGION o COMMUNE."""
    raw = str(text or "").strip()
    if not raw:
        return None, "UNKNOWN"

    data = _index()
    digits = re.fullmatch(r"(?:CL-(?:REG|COM)-)?(\d{2}|\d{5})", raw.upper())
    if digits:
        code = digits.group(1)
        return f"CL-{'REG' if len(code) == 2 else 'COM'}-{code}", "CODE_EXACT"

    key = match_key(raw)
    if not key:
        return None, "UNKNOWN"
    if len(key) > data.get("max_key_len", 45):
        return None, "NOT_A_PLACE_NAME"

    found = data.get("index", {}).get(level, {}).get(key)
    return (found, "VALIDATED_EXACT") if found else (None, "UNRESOLVED_NAME_ONLY")
