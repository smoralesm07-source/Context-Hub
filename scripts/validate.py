from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[1]

def lines(path):
    p=ROOT/path
    if not p.exists(): return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

errors=[]
regions=lines("data/silver/dim_region.jsonl")
sectors=lines("data/silver/dim_sector.jsonl")
maps=lines("data/silver/sector_sii_mapping_v1.jsonl")
sources=json.loads((ROOT/"config/sources.json").read_text(encoding="utf-8"))
if len(regions)!=16: errors.append(f"expected 16 region seed rows, got {len(regions)}")
if len(sectors)!=55: errors.append(f"expected 55 sector rows, got {len(sectors)}")
if not maps: errors.append("sector mapping is empty")
if any(x.get("legal_membership_assertion_allowed") for x in maps):
    errors.append("ACTECO-only mapping improperly allows legal UAF membership assertion")
if any("sermig" in json.dumps(x, ensure_ascii=False).lower() for x in sources):
    errors.append("SERMIG must not be a Context Hub migration source")
if len({x["territory_id"] for x in regions}) != len(regions): errors.append("duplicate region ids")
if len({x["sector_id"] for x in sectors}) != len(sectors): errors.append("duplicate sector ids")
if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(json.dumps({"valid":True,"regions":len(regions),"sectors":len(sectors),"mappings":len(maps),"sources":len(sources)}))
