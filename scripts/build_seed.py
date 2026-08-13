from __future__ import annotations
import csv, json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def write_jsonl(path:Path,rows:list[dict])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")
    tmp.replace(path)

def build()->dict:
    seed=ROOT/"data/seed"
    sectors=[]
    with (seed/"sectors_v1.csv").open(encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            n=int(r["uaf_sector_id"])
            sectors.append({
                "aml_risk_score":None,"context_only":True,"macrofamily":r["macrofamily"],
                "schema_version":"1.0","sector_id":f"UAF-SEC-{n:02d}",
                "source_basis":["UAF_LEY19913_ACTIVITY_LIST","PRIOR_GOVERNED_CROSSWALK"],
                "taxonomy":"LEY_19913_ART3_PRIVATE_SECTOR_ANALYTIC_TAXONOMY",
                "uaf_activity_name":r["uaf_activity_name"],"uaf_sector_id":n,
            })
    sectors.sort(key=lambda x:x["uaf_sector_id"])
    names={x["uaf_sector_id"]:x["uaf_activity_name"] for x in sectors}
    write_jsonl(ROOT/"data/silver/dim_sector.jsonl",sectors)

    overrides={
        31:"Empresas de Depósitos de Valores regidas por Ley 18.876",
        37:"Fintec: Custodia de Instrumentos Financieros",
        38:"Fintec: Intermediación de Instrumentos Financieros",
        39:"Fintec: Plataforma de Financiamiento Colectivo",
        40:"Fintec: Sistemas Alternativos de Transacción",
        41:"Fintec: Proveedores de Iniciación de Pagos",
        42:"Fintec: Otros fiscalizados por CMF",
        47:"Organizaciones Deportivas Profesionales regidas por Ley 20.019",
    }
    def rule(eq:str,use:str):
        if eq=="DIRECTA": return "VALIDATED_RULE","DIRECT_ACTECO_PLUS_EXTERNAL_VALIDATION_REQUIRED",0.9
        if eq=="PARCIAL": return "EMPIRICAL_CANDIDATE","COMPATIBLE_BUT_BROADER_ACTECO",0.9 if use=="MATCH_FUERTE" else 0.7
        if eq=="AMPLIA": return "AMBIGUOUS","BROAD_ACTECO_SCREENING_ONLY",0.7 if use=="CANDIDATO" else 0.4
        return "NO_EQUIVALENCE","NO_DEFENSIBLE_DIRECT_ACTECO",0.4

    mappings=[]
    for path in sorted(seed.glob("sector_sii_mapping_v1_part*.csv")):
        with path.open(encoding="utf-8",newline="") as f:
            for r in csv.DictReader(f):
                n=int(r["uaf_sector_id"]); eq=r["original_equivalence_type"]; use=r["original_use"]
                status,basis,confidence=rule(eq,use)
                mappings.append({
                    "legal_membership_assertion_allowed":False,"mapping_basis":basis,
                    "mapping_confidence":confidence,"mapping_id":r["mapping_id"],"mapping_status":status,
                    "method_note":r["method_note"],"original_equivalence_type":eq,"original_use":use,
                    "required_external_source":r["required_external_source"],"requires_external_validation":True,
                    "reviewed_at":"2026-08-12","schema_version":"1.0","sector_id":f"UAF-SEC-{n:02d}",
                    "sii_activity_code":r["sii_activity_code"].strip() or None,
                    "sii_activity_name":r["sii_activity_name"].strip() or None,
                    "source_sii":"https://www.sii.cl/catastro/codigos.htm",
                    "source_uaf":"https://www.uaf.cl/es-cl/sujetos-obligados/sector-privado/quienes-deben-reportar",
                    "sufficient_to_infer_uaf_obliged_status":False,
                    "uaf_activity_name":overrides.get(n,names[n]),"uaf_sector_id":n,
                    "valid_from":None,"valid_to":None,
                })
    mappings.sort(key=lambda x:x["mapping_id"])
    write_jsonl(ROOT/"data/silver/sector_sii_mapping_v1.jsonl",mappings)
    counts=Counter(x["mapping_status"] for x in mappings)
    status={
        "hub":"SECTOR_HUB","version":"1.0","sector_rows":len(sectors),"mapping_rows":len(mappings),
        "mapping_status_counts":dict(counts),"all_acteco_only_membership_assertions_blocked":True,
        "source_workbook":"maestro_equivalencias_uaf_sii_v0_1.xlsx",
        "context_risk_imported_from_sectorial_exploration":False,
    }
    (ROOT/"data/gold").mkdir(parents=True,exist_ok=True)
    (ROOT/"data/gold/sector_hub_status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return status

if __name__=="__main__":
    print(json.dumps(build(),ensure_ascii=False))
