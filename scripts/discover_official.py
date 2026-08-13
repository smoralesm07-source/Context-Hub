from __future__ import annotations
import io, json, zipfile
from pathlib import Path
import requests
import pandas as pd

UA={'User-Agent':'ContextHubChile/0.2 source-discovery'}

def clean(v):
    if pd.isna(v): return None
    if hasattr(v,'isoformat'):
        try: return v.isoformat()
        except Exception: pass
    return str(v)[:180]

def excel_preview(url, max_sheets=20, max_rows=30, max_cols=20):
    r=requests.get(url,timeout=90,headers=UA); r.raise_for_status(); raw=r.content
    xls=pd.ExcelFile(io.BytesIO(raw)); sheets=[]
    for name in xls.sheet_names[:max_sheets]:
        df=pd.read_excel(io.BytesIO(raw),sheet_name=name,header=None,nrows=max_rows).iloc[:,:max_cols]
        rows=[[clean(v) for v in row] for row in df.itertuples(index=False,name=None)]
        sheets.append({'sheet':str(name),'rows':len(rows),'cols':int(df.shape[1]),'preview':rows})
    return {'status':'CURRENT','bytes':len(raw),'sheet_names':[str(x) for x in xls.sheet_names],'sheets':sheets}

def zip_preview(url, max_files=20):
    r=requests.get(url,timeout=120,headers=UA); r.raise_for_status(); z=zipfile.ZipFile(io.BytesIO(r.content))
    names=z.namelist(); samples=[]
    for n in names[:max_files]:
        info=z.getinfo(n); item={'name':n,'size':info.file_size}
        if info.file_size and info.file_size<20_000_000 and n.lower().endswith(('.txt','.csv')):
            b=z.read(n)[:12000]; text=None
            for enc in ('utf-8-sig','latin-1'):
                try: text=b.decode(enc); break
                except Exception: pass
            if text is not None: item['sample_lines']=text.splitlines()[:8]
        samples.append(item)
    return {'status':'CURRENT','bytes':len(r.content),'files':names,'samples':samples}

def arcgis_preview(url):
    q=url.rstrip('/')+'/query'; params={'where':'1=1','outFields':'CUT_REG,CUT_PROV,CUT_COM,REGION,PROVINCIA,COMUNA','returnGeometry':'false','orderByFields':'CUT_COM','f':'json'}
    r=requests.get(q,params=params,timeout=90,headers=UA); r.raise_for_status(); p=r.json(); features=p.get('features') or []
    return {'status':'CURRENT','feature_count':len(features),'first_features':[x.get('attributes',{}) for x in features[:8]]}

def safe(fn):
    try: return fn()
    except Exception as exc: return {'status':'ERROR','error':f'{type(exc).__name__}: {exc}'}

result={
 'territory_arcgis': safe(lambda: arcgis_preview('https://services3.arcgis.com/IyMwgp3BPBycEJQw/arcgis/rest/services/LIMITE_COMUNAL_IDE_2023/FeatureServer/0')),
 'censo_inmigracion_2024': safe(lambda: excel_preview('https://censo2024.ine.gob.cl/wp-content/uploads/2025/04/D4_Inmigracion-Internacional.xlsx')),
 'enupe_2025': safe(lambda: excel_preview('https://www.bcentral.cl/documents/33528/4240899/ENUPE%2B2025.xlsx/c7e67769-7541-8d2f-6f7d-bc777daf5783?t=1778183770425')),
 'sii_empresas': safe(lambda: zip_preview('https://www.sii.cl/sobre_el_sii/empresas/EMPRESAS.zip')),
}
print('OFFICIAL_SOURCE_DISCOVERY_BEGIN')
print(json.dumps(result,ensure_ascii=False))
print('OFFICIAL_SOURCE_DISCOVERY_END')
