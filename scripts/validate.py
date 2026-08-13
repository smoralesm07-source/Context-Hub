from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path: str) -> Path:
    p = ROOT / path
    if not p.exists():
        raise SystemExit(f"Falta archivo requerido: {path}")
    return p


def main() -> None:
    require("config/sources.json")
    regions = json.loads(require("data/reference/regions_chile.json").read_text(encoding="utf-8"))
    assert len(regions) == 16, "Territory Hub debe contener 16 regiones"
    assert len({r["territory_id"] for r in regions}) == len(regions)
    assert all(r["territory_id"].startswith("CL-REG-") for r in regions)

    sources = json.loads(require("config/sources.json").read_text(encoding="utf-8"))
    assert all(s.get("source_id") != "SERMIG" for s in sources["sources"])
    assert any(x.get("source_id") == "SERMIG" for x in sources.get("excluded_sources", []))

    for path in (
        "src/context_hub/migration.py",
        "src/context_hub/economic.py",
        "src/context_hub/cash.py",
        "src/context_hub/territory.py",
        "src/context_hub/sector.py",
    ):
        require(path)
    print(json.dumps({"valid": True, "regions": len(regions), "sources": len(sources["sources"])}))


if __name__ == "__main__":
    main()
