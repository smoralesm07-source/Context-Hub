"""Resolución gobernada de texto libre territorial hacia claves CUT.

Este módulo es el punto único donde el ecosistema traduce una glosa territorial
(«Región del Biobío», «O'Higgins», «VIII») a una clave canónica `CL-REG-*` o
`CL-COM-*`. Los radares lo consumen en vez de mantener su propia tabla de alias.

Tres reglas de gobierno, no negociables:

1. **Sólo igualdad exacta sobre la forma normalizada.** No hay distancia de
   edición, ni subcadenas, ni «el más parecido». Lo que no cruza queda
   `UNRESOLVED` y se reporta como brecha.

2. **La resolución es consciente del nivel.** Siete nombres de región son
   además nombres de comuna, y uno de ellos cruza regiones: «Los Lagos» es una
   comuna de la Región de Los Ríos. Un índice plano de nombre a clave asignaría
   ese dato a la región equivocada. Por eso el llamador declara el nivel que
   está resolviendo, y `level="ANY"` devuelve `AMBIGUOUS_LEVEL` en vez de
   adivinar.

3. **La ambigüedad nunca se resuelve por desempate.** Si una glosa apunta a más
   de un territorio, el resultado es no resuelto con la razón explícita.

La forma normalizada elimina acentos, mayúsculas y **toda** puntuación y
espacio. Eso hace que «Bío-Bío», «BIO BIO» y «Biobío» compartan clave, y que
«O'Higgins» no se rompa en dos palabras, que es exactamente el modo en que
fallaban los adaptadores privados de cada radar.
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

# Prefijos administrativos que no forman parte del nombre del territorio.
# Se retiran sobre la forma con espacios, antes de compactar la clave.
_PREFIXES = (
    "REGION DE LA", "REGION DEL", "REGION DE", "REGION",
    "PROVINCIA DE LA", "PROVINCIA DEL", "PROVINCIA DE", "PROVINCIA",
    "COMUNA DE LA", "COMUNA DEL", "COMUNA DE", "COMUNA",
    "DE LA", "DEL", "DE",
)

# Una glosa mucho más larga que el topónimo más largo del país no es un nombre
# de lugar: es texto de extracción arrastrado. Se rechaza sin intentar cruzarla.
# El máximo real sobre las 346 comunas y 16 regiones publicadas es 35 caracteres
# («Aysén del General Carlos Ibáñez del Campo»); 45 deja margen para nombres
# oficiales más largos sin dejar pasar párrafos completos.
MAX_KEY_LEN = 45

LEVELS = ("REGION", "PROVINCE", "COMMUNE", "ANY")
_INDEXED_LEVELS = ("REGION", "PROVINCE", "COMMUNE")

# Numerales romanos de región. Se reconocen como token suelto dentro de una
# glosa compuesta del tipo «XIII REGION METROPOLITANA», que publica el SII.
ROMANS = frozenset(
    ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI")
)
_REGION_WORDS = frozenset(("REGION", "REGIONES", "REG"))


def decompose_region(spaced: str) -> list[str]:
    """Descompone una glosa regional compuesta en sus señales independientes.

    «XIII REGION METROPOLITANA» lleva dos señales que deben coincidir: el
    numeral romano y el nombre. Devolverlas por separado permite exigir acuerdo
    en vez de creerle a una sola.
    """
    tokens = spaced.split()
    if not tokens:
        return []
    romans = [t for t in tokens if t in ROMANS]
    rest = [t for t in tokens if t not in ROMANS and t not in _REGION_WORDS]
    keys = list(romans)
    if rest:
        remainder = strip_prefix(" ".join(rest)).replace(" ", "")
        if remainder:
            keys.append(remainder)
    return keys


@dataclass(frozen=True)
class Resolution:
    """Resultado de resolver una glosa territorial."""

    territory_id: str | None
    level: str | None
    method: str
    confidence: float
    source_text: str
    reason: str | None = None

    @property
    def resolved(self) -> bool:
        return self.territory_id is not None


def spaced_form(value: object) -> str:
    """Mayúsculas sin acentos, con la puntuación convertida en espacio."""
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").upper()
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def strip_prefix(spaced: str) -> str:
    """Retira un prefijo administrativo inicial, una sola vez."""
    for prefix in _PREFIXES:
        if spaced == prefix:
            return ""
        if spaced.startswith(prefix + " "):
            return spaced[len(prefix) + 1:].strip()
    return spaced


def match_key(value: object) -> str:
    """Clave de cruce: sin acentos, sin caso, sin puntuación y sin espacios."""
    return strip_prefix(spaced_form(value)).replace(" ", "")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class TerritoryResolver:
    """Índices por nivel construidos desde las dimensiones canónicas y los alias."""

    def __init__(self, regions: list[dict], communes: list[dict], aliases: list[dict],
                 provinces: list[dict] | None = None):
        self._index: dict[str, dict[str, set[str]]] = {lv: {} for lv in _INDEXED_LEVELS}
        self._method: dict[tuple[str, str], str] = {}

        for row in regions:
            self._add("REGION", row["canonical_name"], row["territory_id"], "VALIDATED_EXACT")
        for row in communes:
            self._add("COMMUNE", row["canonical_name"], row["territory_id"], "VALIDATED_EXACT")

        # Las provincias no tienen tabla propia: se derivan de las comunas, que
        # ya traen province_id y province_name desde CUT.
        if provinces is None:
            provinces = []
            seen_prov: set[str] = set()
            for row in communes:
                pid = row.get("province_id")
                if pid and pid not in seen_prov:
                    seen_prov.add(pid)
                    provinces.append({"territory_id": pid, "canonical_name": row.get("province_name")})
        for row in provinces:
            if row.get("canonical_name"):
                self._add("PROVINCE", row["canonical_name"], row["territory_id"], "VALIDATED_EXACT")

        for row in aliases:
            if row.get("status", "ACTIVE") != "ACTIVE":
                continue
            level = row.get("territory_level")
            if not level:
                # Compatibilidad con alias antiguos sin nivel: se infiere de la clave.
                level = "REGION" if str(row["territory_id"]).startswith("CL-REG-") else "COMMUNE"
            if level in self._index:
                self._add(level, row["alias"], row["territory_id"], "VALIDATED_ALIAS")

    def _add(self, level: str, name: object, territory_id: str, method: str) -> None:
        key = match_key(name)
        if not key:
            return
        self._index[level].setdefault(key, set()).add(territory_id)
        # El nombre canónico gana sobre el alias si ambos producen la misma clave.
        if self._method.get((level, key)) != "VALIDATED_EXACT":
            self._method[(level, key)] = method

    def collisions(self) -> dict[str, dict[str, set[str]]]:
        """Claves que apuntan a más de un territorio dentro de un mismo nivel."""
        return {
            level: {k: v for k, v in index.items() if len(v) > 1}
            for level, index in self._index.items()
        }

    def cross_level_keys(self) -> set[str]:
        """Claves presentes en más de un nivel; irresolubles sin declarar nivel."""
        seen: dict[str, int] = {}
        for index in self._index.values():
            for key in index:
                seen[key] = seen.get(key, 0) + 1
        return {k for k, n in seen.items() if n > 1}

    def _lookup(self, level: str, key: str) -> set[str]:
        return self._index[level].get(key, set())

    def _resolve_compound_region(self, raw: str) -> Resolution | None:
        """Resuelve una glosa regional que trae numeral y nombre a la vez.

        Devuelve `None` si la glosa no es compuesta, para que el llamador siga
        su curso normal. Si las dos señales apuntan a regiones distintas, no se
        elige una: se devuelve `CONFLICTING_SIGNALS`.
        """
        candidates = decompose_region(spaced_form(raw))
        if len(candidates) < 2:
            return None
        found: set[str] = set()
        for candidate in candidates:
            found |= self._lookup("REGION", candidate)
        if not found:
            return None
        if len(found) > 1:
            return Resolution(None, None, "UNRESOLVED", 0.0, raw, "CONFLICTING_SIGNALS")
        return Resolution(next(iter(found)), "REGION", "VALIDATED_COMPOUND", 1.0, raw)

    def resolve(self, text: object, level: str = "ANY") -> Resolution:
        """Resuelve una glosa. `level` acota el índice consultado."""
        level = str(level).upper()
        if level not in LEVELS:
            raise ValueError(f"Nivel no soportado: {level}")
        raw = str(text or "").strip()

        # Un código CUT ya canónico entra directo, sin pasar por nombres.
        # La longitud determina el nivel: 2 región, 3 provincia, 5 comuna.
        direct = re.fullmatch(r"(?:CL-(?:REG|PROV|COM)-)?(\d{2}|\d{3}|\d{5})", raw.upper())
        if direct:
            digits = direct.group(1)
            found = {2: "REGION", 3: "PROVINCE", 5: "COMMUNE"}[len(digits)]
            prefix = {"REGION": "REG", "PROVINCE": "PROV", "COMMUNE": "COM"}[found]
            if level in (found, "ANY"):
                return Resolution(f"CL-{prefix}-{digits}", found, "CODE_EXACT", 1.0, raw)

        if not raw:
            return Resolution(None, None, "UNRESOLVED", 0.0, raw, "EMPTY")

        key = match_key(raw)
        if not key:
            return Resolution(None, None, "UNRESOLVED", 0.0, raw, "EMPTY")
        if len(key) > MAX_KEY_LEN:
            return Resolution(None, None, "UNRESOLVED", 0.0, raw, "NOT_A_PLACE_NAME")

        levels = _INDEXED_LEVELS if level == "ANY" else (level,)
        hits = [(lv, self._index[lv][key]) for lv in levels if key in self._index[lv]]

        if not hits:
            # Glosa regional compuesta del tipo «XIII REGION METROPOLITANA»:
            # se exige que el numeral romano y el nombre apunten al mismo lugar.
            if level in ("REGION", "ANY"):
                compound = self._resolve_compound_region(raw)
                if compound is not None:
                    return compound
            return Resolution(None, None, "UNRESOLVED", 0.0, raw, "NO_MATCH")
        if len(hits) > 1:
            # «Valparaíso» es región y comuna. Sin nivel declarado no se elige.
            return Resolution(None, None, "UNRESOLVED", 0.0, raw, "AMBIGUOUS_LEVEL")

        found_level, ids = hits[0]
        if len(ids) > 1:
            return Resolution(None, None, "UNRESOLVED", 0.0, raw, "AMBIGUOUS_TERRITORY")

        method = self._method[(found_level, key)]
        return Resolution(next(iter(ids)), found_level, method, 1.0, raw)


def load_resolver(root: str | Path) -> TerritoryResolver:
    """Carga el resolver desde las dimensiones publicadas del Context Hub."""
    base = Path(root)
    silver = base / "data" / "silver"
    aliases = _read_jsonl(silver / "territory_aliases.jsonl")
    if not aliases:
        seed = base / "data" / "seed" / "territory_aliases_v1.csv"
        if seed.exists():
            with seed.open(encoding="utf-8", newline="") as handle:
                aliases = list(csv.DictReader(handle))
    return TerritoryResolver(
        regions=_read_jsonl(silver / "dim_region.jsonl"),
        communes=_read_jsonl(silver / "dim_territory.jsonl"),
        aliases=aliases,
    )


def export_index(resolver: TerritoryResolver) -> dict:
    """Índice plano y portable para que los radares resuelvan sin importar este paquete.

    Es el artefacto de interoperabilidad: un radar lo lee y aplica `match_key`
    sobre su glosa. Se publica con la política y las ambigüedades declaradas,
    de modo que un consumidor no pueda usarlo creyendo que resuelve todo.
    """
    return {
        "schema_version": "1.0",
        "artifact": "TERRITORY_RESOLUTION_INDEX",
        "canonical_key_source": "SUBDERE_CUT",
        "resolution_policy": "EXACT_MATCH_ON_NORMALIZED_KEY_ONLY",
        "fuzzy_match_promoted_to_truth": False,
        "key_recipe": (
            "NFD, eliminar diacríticos, mayúsculas, reemplazar [^A-Z0-9] por espacio, "
            "retirar un prefijo administrativo inicial (REGION/PROVINCIA/COMUNA/DE/DEL/DE LA), "
            "eliminar los espacios restantes"
        ),
        "max_key_len": MAX_KEY_LEN,
        "level_is_required": True,
        "levels": list(_INDEXED_LEVELS),
        # Para resolver glosas compuestas del tipo «XIII REGION METROPOLITANA»:
        # el adaptador separa numeral y nombre, y exige que ambos coincidan.
        "compound_region": {
            "romans": sorted(ROMANS, key=lambda r: (len(r), r)),
            "region_words": sorted(_REGION_WORDS),
            "policy": "ALL_SIGNALS_MUST_AGREE_OR_CONFLICTING_SIGNALS",
        },
        "cross_level_ambiguous_keys": sorted(resolver.cross_level_keys()),
        "index": {
            level: {k: next(iter(v)) for k, v in sorted(index.items()) if len(v) == 1}
            for level, index in resolver._index.items()
        },
    }


def resolution_report(resolver: TerritoryResolver, values, level: str = "ANY") -> dict:
    """Resuelve un conjunto de glosas y resume cobertura y brechas.

    Pensado para que cada radar publique su tasa real de resolución territorial
    en vez de declarar una etapa cualitativa en el manifiesto.
    """
    seen: dict[str, Resolution] = {}
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen[text] = resolver.resolve(text, level)

    resolved = {k: v for k, v in seen.items() if v.resolved}
    gaps = sorted(
        ({"source_text": k, "reason": v.reason} for k, v in seen.items() if not v.resolved),
        key=lambda g: g["source_text"],
    )
    total = len(seen)
    return {
        "distinct_values": total,
        "resolved": len(resolved),
        "unresolved": len(gaps),
        "resolution_pct": round(len(resolved) / total * 100, 1) if total else None,
        "by_method": {
            m: sum(1 for r in resolved.values() if r.method == m)
            for m in sorted({r.method for r in resolved.values()})
        },
        "gaps": gaps,
    }
