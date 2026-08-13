import sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from context_hub.censo_migration import parse_region_totals, parse_commune_totals


def test_censo_parser_region_and_commune(tmp_path):
    path=tmp_path/"censo.xlsx"
    regions=[]
    for i in range(1,17):
        regions.append({"Código región":i,"Región":f"R{i}","Inmigrantes internacionales":100+i,"Hombres":40,"Mujeres":60,"Razón hombre-mujer":66.7,"Lugar de nacimiento no declarado":1})
    communes=[]
    for i in range(346):
        reg=(i%16)+1; prov=reg*10+1; com=10000+i+1
        communes.append({"Código región":reg,"Región":f"R{reg}","Código provincia":prov,"Provincia":f"P{prov}","Codigo comuna":com,"Comuna":f"C{com}","País o continente de nacimiento":"Total nacidos fuera del país","Inmigrantes internacionales":i})
    with pd.ExcelWriter(path,engine="openpyxl") as xw:
        pd.DataFrame(regions).to_excel(xw,sheet_name="1",index=False,startrow=3)
        pd.DataFrame(communes).to_excel(xw,sheet_name="4",index=False,startrow=3)
    rr=parse_region_totals(path); cr=parse_commune_totals(path)
    assert len(rr)==16
    assert len(cr)==346
    assert rr[0]["territory_id"].startswith("CL-REG-")
    assert cr[0]["territory_id"].startswith("CL-COM-")
