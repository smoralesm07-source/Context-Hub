from __future__ import annotations
import argparse, json
from pathlib import Path
from .io import read_jsonl, write_jsonl, write_json
from .migration import migration_exposure, exposure_label
from .economic import enrich_peer_context, join_macro_context
from .cash import validate_geography, add_cash_trend, sector_cash_exposure
from .territory import parse_subdere_cut_xls, parse_arcgis_features
from .sources import download_preserve_last_good, query_arcgis_features
from .source_profile import profile_excel
from .censo_migration import parse_region_totals, parse_commune_totals, territory_rows_from_commune_totals

ROOT=Path(__file__).resolve().parents[2]
def _load_json(path:Path): return json.loads(path.read_text(encoding="utf-8"))

def materialize_staging()->dict:
    result={}
    migration_in=read_jsonl(ROOT/"data/staging/migration_context.jsonl")
    migration_out=[]
    for r in migration_in:
        x=migration_exposure(r); x["exposure_label"]=exposure_label(x["migration_exposure_index_v1"],x["score_coverage"])
        migration_out.append(x)
    write_jsonl(ROOT/"data/gold/migration_context_v1.jsonl",migration_out)
    result["migration_rows"]=len(migration_out)

    entity_in=read_jsonl(ROOT/"data/staging/economic_entity_context.jsonl")
    macro_in=read_jsonl(ROOT/"data/staging/economic_macro_context.jsonl")
    entity_joined=join_macro_context(entity_in,macro_in) if entity_in else []
    economic_out=enrich_peer_context(entity_joined,min_peer_count=20) if entity_joined else []
    write_jsonl(ROOT/"data/gold/economic_peer_context_v1.jsonl",economic_out)
    result["economic_rows"]=len(economic_out)
    result["economic_macro_rows"]=len(macro_in)

    cash_in=read_jsonl(ROOT/"data/staging/cash_context.jsonl")
    for r in cash_in: validate_geography(r)
    cash_out=add_cash_trend(cash_in) if cash_in else []
    write_jsonl(ROOT/"data/gold/cash_context_v1.jsonl",cash_out)
    result["cash_rows"]=len(cash_out)

    sector_cash_in=read_jsonl(ROOT/"data/staging/cash_sector_context.jsonl")
    sector_cash_out=[sector_cash_exposure(r) for r in sector_cash_in]
    write_jsonl(ROOT/"data/gold/cash_sector_context_v1.jsonl",sector_cash_out)
    result["cash_sector_rows"]=len(sector_cash_out)
    return result

def _publish_territory(rows:list[dict],source_id:str,source_tier:str)->dict:
    rows=sorted({r["territory_id"]:r for r in rows}.values(), key=lambda x:x["commune_code"])
    write_jsonl(ROOT/"data/silver/dim_territory.jsonl",rows)
    status={
        "hub":"TERRITORY_HUB","version":"1.0","commune_rows":len(rows),
        "region_rows":len({r["region_code"] for r in rows}),
        "province_rows":len({r["province_code"] for r in rows}),
        "status":"READY" if len(rows)==346 else "PARTIAL_COVERAGE",
        "canonical_key_source":"SUBDERE_CUT","materialization_source":source_id,
        "materialization_source_tier":source_tier,
        "canonical_commune_format":"CL-COM-{CUT_COM}",
        "name_is_key":False,"fuzzy_match_promoted_to_truth":False,
    }
    write_json(ROOT/"data/gold/territory_hub_status.json",status); return status

def refresh_migration_source(sources:list[dict])->dict:
    source=next(x for x in sources if x["source_id"]=="INE_CENSO2024_INMIGRACION")
    target=ROOT/"data/bronze/D4_Inmigracion-Internacional.xlsx"
    status_path=ROOT/"data/gold/source_status_INE_CENSO2024_INMIGRACION.json"
    status=download_preserve_last_good(source,target,status_path)
    result={"download":status}
    if not target.exists(): return result
    try:
        profile=profile_excel(target)
        profile.update({"source_id":"INE_CENSO2024_INMIGRACION","source_owner":"INE","context_only":True,"aml_interpretation":"NONE"})
        write_json(ROOT/"data/gold/source_profile_INE_CENSO2024_INMIGRACION.json",profile)
        result["profile"]={"status":"READY","sheet_count":profile["sheet_count"],"sheet_names":profile["sheet_names"]}
    except Exception as exc:
        result["profile"]={"status":"ERROR","error":f"{type(exc).__name__}: {exc}"}
    try:
        region_rows=parse_region_totals(target)
        commune_rows=parse_commune_totals(target)
        write_jsonl(ROOT/"data/gold/migration_region_censo2024_v1.jsonl",region_rows)
        write_jsonl(ROOT/"data/gold/migration_commune_censo2024_v1.jsonl",commune_rows)
        result["materialized"]={"status":"READY","region_rows":len(region_rows),"commune_rows":len(commune_rows),"score_calculated":False}
    except Exception as exc:
        result["materialized"]={"status":"ERROR","error":f"{type(exc).__name__}: {exc}"}
    return result

def refresh_territory(sources:list[dict])->dict:
    primary=next(x for x in sources if x["source_id"]=="SUBDERE_CUT")
    candidates=[
        next(x for x in sources if x["source_id"]=="IDE_CHILE_DPA_2023"),
        next(x for x in sources if x["source_id"]=="MOP_IDE_DPA_SUBDERE"),
    ]
    target=ROOT/"data/bronze/CUT_2018_v04.xls"
    primary_status=download_preserve_last_good(primary,target,ROOT/"data/gold/source_status_SUBDERE_CUT.json")
    if target.exists():
        try:
            rows=parse_subdere_cut_xls(target)
            if len(rows)>=345:
                return {"primary":primary_status,"hub":_publish_territory(rows,"SUBDERE_CUT","PRIMARY_OFFICIAL")}
        except Exception as exc:
            primary_status["parse_error"]=f"{type(exc).__name__}: {exc}"
    attempts=[]; best_rows=[]; best_source=None; best_tier=None
    for candidate in candidates:
        try:
            features,status=query_arcgis_features(candidate)
            rows=parse_arcgis_features(features,candidate["source_id"])
            write_json(ROOT/f"data/gold/source_status_{candidate['source_id']}.json",status)
            attempts.append({"source_id":candidate["source_id"],"feature_count":len(rows),"status":"CURRENT"})
            if len(rows)>len(best_rows):
                best_rows=rows; best_source=candidate["source_id"]
                best_tier="OFFICIAL_SECONDARY" if candidate["source_id"]=="MOP_IDE_DPA_SUBDERE" else "OFFICIAL_GEOGRAPHIC_SECONDARY"
            if len(rows)>=346: break
        except Exception as exc:
            attempts.append({"source_id":candidate["source_id"],"status":"ERROR","error":f"{type(exc).__name__}: {exc}"})
    # The MOP/SUBDERE layer intentionally excludes Antártica (345 communes). If needed,
    # add only missing exact CUT-coded communes from the official INE Censo workbook.
    censo_path=ROOT/"data/bronze/D4_Inmigracion-Internacional.xlsx"
    if best_rows and len(best_rows)<346 and censo_path.exists():
        try:
            censo_territory=territory_rows_from_commune_totals(parse_commune_totals(censo_path))
            existing={r["territory_id"] for r in best_rows}
            additions=[r for r in censo_territory if r["territory_id"] not in existing]
            best_rows=best_rows+additions
            attempts.append({"source_id":"INE_CENSO2024_INMIGRACION","status":"AUGMENTED_EXACT_CUT","added_rows":len(additions)})
            if additions: best_source=f"{best_source}+INE_CENSO2024_INMIGRACION"
        except Exception as exc:
            attempts.append({"source_id":"INE_CENSO2024_INMIGRACION","status":"ERROR","error":f"{type(exc).__name__}: {exc}"})
    result={"primary":primary_status,"attempts":attempts}
    if best_rows:
        result["hub"]=_publish_territory(best_rows,best_source or "UNKNOWN",best_tier or "OFFICIAL_SECONDARY")
    return result

def run(network:bool=False)->dict:
    sources=_load_json(ROOT/"config/sources.json"); result={"network":network}
    if network:
        result["migration_source"]=refresh_migration_source(sources)
        result["territory_refresh"]=refresh_territory(sources)
    result.update(materialize_staging())
    write_json(ROOT/"data/gold/last_run.json",result); return result

def main():
    p=argparse.ArgumentParser(); p.add_argument("--network",action="store_true"); args=p.parse_args()
    print(json.dumps(run(args.network),ensure_ascii=False,indent=2))
if __name__=="__main__": main()
