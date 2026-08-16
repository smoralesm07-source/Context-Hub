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
    assert all(not v for v in resolver.collisions().values())
    assert set(resolver.collisions()) == {"REGION", "PROVINCE", "COMMUNE"}
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


# ── Glosa regional compuesta y nivel provincia ──────────────────────────────

def test_compound_region_gloss_needs_both_signals_to_agree():
    """«XIII REGION METROPOLITANA» trae numeral y nombre en un solo campo.

    Es el formato que publica el SII. Las dos señales son independientes, así
    que se exige que apunten al mismo lugar en vez de creerle a una sola.
    """
    r = load_resolver(__import__("pathlib").Path(__file__).resolve().parents[1])
    assert r.resolve("XIII REGION METROPOLITANA", "REGION").territory_id == "CL-REG-13"
    assert r.resolve("XIII REGION METROPOLITANA", "REGION").method == "VALIDATED_COMPOUND"
    assert r.resolve("IV REGION COQUIMBO", "REGION").territory_id == "CL-REG-04"
    # Numeral y nombre en desacuerdo: no se elige ninguno.
    assert r.resolve("IV REGION METROPOLITANA", "REGION").reason == "CONFLICTING_SIGNALS"


def test_province_level_resolves_and_is_separate_from_commune():
    """28 nombres de provincia son además nombres de comuna."""
    r = load_resolver(__import__("pathlib").Path(__file__).resolve().parents[1])
    assert r.resolve("Santiago", "PROVINCE").territory_id == "CL-PROV-131"
    assert r.resolve("Santiago", "COMMUNE").territory_id == "CL-COM-13101"
    assert r.resolve("Santiago", "ANY").reason == "AMBIGUOUS_LEVEL"
    assert r.resolve("Limarí", "PROVINCE").territory_id == "CL-PROV-043"


def test_province_code_enters_directly():
    r = load_resolver(__import__("pathlib").Path(__file__).resolve().parents[1])
    assert r.resolve("CL-PROV-131", "PROVINCE").method == "CODE_EXACT"


def test_reference_adapter_agrees_with_the_hub():
    """El adaptador vendorizado debe resolver idéntico al resolver del hub.

    Los radares copian `interop/territory_adapter_reference.py` en vez de
    importar este paquete, así que la deriva entre ambos es el riesgo real de
    ese diseño. Este test la detecta.
    """
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "territory_adapter_reference", root / "interop" / "territory_adapter_reference.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    adapter.INDEX_PATH = root / "data" / "gold" / "territory_resolution_index_v1.json"
    adapter._index.cache_clear()

    resolver = load_resolver(root)
    corpus = [
        ("Biobío", "REGION"), ("BIO-BÍO", "REGION"), ("Región del Biobío", "REGION"),
        ("O'Higgins", "REGION"), ("O'Higgins", "COMMUNE"), ("VIII", "REGION"), ("RM", "REGION"),
        ("XIII REGION METROPOLITANA", "REGION"), ("IV REGION COQUIMBO", "REGION"),
        ("IV REGION METROPOLITANA", "REGION"), ("Santiago", "PROVINCE"), ("Santiago", "COMMUNE"),
        ("Limarí", "PROVINCE"), ("LAS CONDES", "COMMUNE"), ("OVALLE", "COMMUNE"),
        ("Los Lagos", "REGION"), ("Los Lagos", "COMMUNE"), ("13", "REGION"),
        ("CL-PROV-131", "PROVINCE"), ("13101", "COMMUNE"),
        ("Region Inventada", "REGION"), ("", "REGION"), ("Bío", "REGION"),
        (", oficina del SAG a cargo,", "REGION"),
        ("DE ARICA Y PARINACOTA. _JUNIO 2026_ Documento Asociado Descargar documento", "REGION"),
    ]
    for text, level in corpus:
        hub = resolver.resolve(text, level)
        vendored_id, vendored_status = adapter.resolve(text, level)
        assert hub.territory_id == vendored_id, f"{text!r} ({level}): id difiere"
        expected = hub.method if hub.resolved else (hub.reason or "UNRESOLVED")
        # El vocabulario del adaptador es más grueso a propósito: el índice
        # exportado aplana nombre canónico y alias en un solo mapa, de modo que
        # no puede distinguir su procedencia. Lo que sí debe coincidir siempre
        # es el territory_id, que es lo que entra a la capa de fusión.
        expected = {
            "NO_MATCH": "UNRESOLVED_NAME_ONLY",
            "EMPTY": "UNKNOWN",
            "VALIDATED_ALIAS": "VALIDATED_EXACT",
        }.get(expected, expected)
        assert vendored_status == expected, f"{text!r} ({level}): estado difiere"
