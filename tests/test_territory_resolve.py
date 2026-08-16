import pytest

from context_hub.territory_resolve import (
    TerritoryResolver,
    load_resolver,
    match_key,
    resolution_report,
)

REGIONS = [
    {"territory_id": "CL-REG-06", "canonical_name": "Libertador General Bernardo O'Higgins"},
    {"territory_id": "CL-REG-08", "canonical_name": "Biobío"},
    {"territory_id": "CL-REG-10", "canonical_name": "Los Lagos"},
    {"territory_id": "CL-REG-13", "canonical_name": "Metropolitana de Santiago"},
]
COMMUNES = [
    {"territory_id": "CL-COM-11302", "canonical_name": "O'Higgins"},
    {"territory_id": "CL-COM-13101", "canonical_name": "Santiago"},
    {"territory_id": "CL-COM-14104", "canonical_name": "Los Lagos"},
]
ALIASES = [
    {"alias": "VIII", "territory_id": "CL-REG-08", "territory_level": "REGION", "status": "ACTIVE"},
    {"alias": "RM", "territory_id": "CL-REG-13", "territory_level": "REGION", "status": "ACTIVE"},
    {"alias": "O'Higgins", "territory_id": "CL-REG-06", "territory_level": "REGION", "status": "ACTIVE"},
    {"alias": "Retirado", "territory_id": "CL-REG-13", "territory_level": "REGION", "status": "RETIRED"},
]


@pytest.fixture
def resolver():
    return TerritoryResolver(REGIONS, COMMUNES, ALIASES)


def test_key_absorbs_punctuation_accents_and_spacing():
    # Las tres grafías del Biobío colapsan a la misma clave.
    assert match_key("Biobío") == match_key("BIO-BÍO") == match_key("Bio Bio") == "BIOBIO"
    # El apóstrofo no debe partir el nombre en dos palabras.
    assert match_key("O'Higgins") == "OHIGGINS"


def test_administrative_prefix_is_stripped():
    assert match_key("Región del Biobío") == "BIOBIO"
    assert match_key("REGION DE LOS LAGOS") == "LOSLAGOS"
    assert match_key("Comuna de Santiago") == "SANTIAGO"


def test_canonical_name_resolves_exact(resolver):
    r = resolver.resolve("Biobío", "REGION")
    assert (r.territory_id, r.method, r.confidence) == ("CL-REG-08", "VALIDATED_EXACT", 1.0)


def test_governed_alias_resolves(resolver):
    assert resolver.resolve("VIII", "REGION").territory_id == "CL-REG-08"
    assert resolver.resolve("rm", "REGION").method == "VALIDATED_ALIAS"


def test_retired_alias_is_ignored(resolver):
    assert resolver.resolve("Retirado", "REGION").reason == "NO_MATCH"


def test_same_name_at_two_levels_needs_the_level():
    """«Los Lagos» es región y además comuna de OTRA región.

    Es el caso que un índice plano de nombre a clave resolvería mal: asignaría
    la comuna de Los Ríos a la Región de Los Lagos.
    """
    r = TerritoryResolver(REGIONS, COMMUNES, ALIASES)
    assert r.resolve("Los Lagos", "REGION").territory_id == "CL-REG-10"
    assert r.resolve("Los Lagos", "COMMUNE").territory_id == "CL-COM-14104"
    assert r.resolve("Los Lagos", "ANY").reason == "AMBIGUOUS_LEVEL"


def test_alias_and_commune_sharing_a_name_stay_separate(resolver):
    assert resolver.resolve("O'Higgins", "REGION").territory_id == "CL-REG-06"
    assert resolver.resolve("O'Higgins", "COMMUNE").territory_id == "CL-COM-11302"
    assert resolver.resolve("O'Higgins", "ANY").reason == "AMBIGUOUS_LEVEL"


def test_cut_code_enters_directly(resolver):
    assert resolver.resolve("13", "REGION").method == "CODE_EXACT"
    assert resolver.resolve("CL-COM-13101", "COMMUNE").territory_id == "CL-COM-13101"
    assert resolver.resolve("13101", "COMMUNE").territory_id == "CL-COM-13101"


def test_no_fuzzy_match(resolver):
    """Una glosa parecida no se promueve: se rechaza."""
    for text in ("Biobio Region Sur", "Metropolit", "Santiag", "Bío"):
        assert resolver.resolve(text, "REGION").territory_id is None


def test_extraction_garbage_is_refused(resolver):
    """Texto arrastrado por el extractor no debe cruzar contra ningún topónimo."""
    garbage = "DE ARICA Y PARINACOTA. _JUNIO 2026_ Documento Asociado Descargar documento"
    result = resolver.resolve(garbage, "REGION")
    assert result.territory_id is None
    assert result.reason == "NOT_A_PLACE_NAME"
    assert resolver.resolve(", oficina del SAG a cargo,", "REGION").reason == "NO_MATCH"


def test_empty_input(resolver):
    assert resolver.resolve(None, "REGION").reason == "EMPTY"
    assert resolver.resolve("   ", "REGION").reason == "EMPTY"


def test_unknown_level_rejected(resolver):
    with pytest.raises(ValueError):
        resolver.resolve("Biobío", "PLANET")


def test_report_summarises_coverage_and_gaps(resolver):
    report = resolution_report(resolver, ["Biobío", "VIII", "Bío", "Biobío", ""], "REGION")
    assert report["distinct_values"] == 3          # cadena vacía descartada, duplicado colapsado
    assert report["resolved"] == 2
    assert report["resolution_pct"] == pytest.approx(66.7)
    assert [g["source_text"] for g in report["gaps"]] == ["Bío"]


def test_real_hub_has_no_within_level_collisions():
    """Las 346 comunas y 16 regiones publicadas deben ser inequívocas por nivel."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    resolver = load_resolver(root)
    assert resolver.collisions() == {"REGION": {}, "COMMUNE": {}}
    # Y las claves que sí viven en dos niveles quedan documentadas, no ocultas.
    assert "LOSLAGOS" in resolver.cross_level_keys()


def test_length_guard_stays_above_the_longest_real_toponym():
    """El guardia de longitud no debe empezar a rechazar nombres válidos."""
    import json
    from pathlib import Path

    from context_hub.territory_resolve import MAX_KEY_LEN

    root = Path(__file__).resolve().parents[1]
    names = []
    for f in ("dim_territory.jsonl", "dim_region.jsonl"):
        path = root / "data" / "silver" / f
        names += [json.loads(l)["canonical_name"] for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert max(len(match_key(n)) for n in names) < MAX_KEY_LEN
