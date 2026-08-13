from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "reference"
DOCS = ROOT / "docs" / "data"


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    regions_path = DATA / "regions_chile.json"
    regions = json.loads(regions_path.read_text(encoding="utf-8"))
    (DOCS / "territory_hub_regions_v1.json").write_text(
        json.dumps(regions, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    status = {
        "interop_version": "1.0",
        "component": "CONTEXT_HUB",
        "territory_hub": {
            "seed_regions": len(regions),
            "canonical_patterns": ["CL-REG-*", "CL-PROV-*", "CL-COM-*"],
            "name_is_key": False,
            "full_cut_status": "DISCOVERY_PENDING"
        },
        "guardrails": {
            "context_is_aml_risk": False,
            "missing_is_zero": False,
            "source_failure_erases_last_good": False,
            "nationality_as_aml_proxy": False,
            "cross_grain_downscaling": False
        }
    }
    (DOCS / "context_hub_status_v1.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    main()
