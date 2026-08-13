# Contratos normalizados de entrada

Los adaptadores externos deben llevar sus fuentes a estos contratos antes de calcular contexto.

## `data/staging/migration_context.jsonl`

```json
{
  "territory_id": "CL-REG-15",
  "territory_level": "REGION",
  "period": "2025",
  "foreign_resident_share_percentile": 82.0,
  "international_passenger_intensity_percentile": 97.0,
  "migration_change_percentile": null,
  "source_ids": ["INE_CENSO2024_INMIGRACION", "INE_MIP_PDI"]
}
```

## `data/staging/economic_entity_context.jsonl`

```json
{
  "entity_id": "ENT-RUT-76000000-0",
  "year": 2024,
  "activity_code": "000000",
  "region_code": "13",
  "commune_code": "13101",
  "sales_band_rank": 9,
  "workers": 4,
  "start_year": 2022,
  "company_sales_band_delta_1y": 2
}
```

`sales_band_rank` debe ser ordinal y gobernado por la tabla de tramos SII.

## `data/staging/cash_context.jsonl`

```json
{
  "territory_id": "CL-MACROZONE-NORTH",
  "territory_level": "MACROZONE",
  "source_representativeness": "MACROZONE",
  "period": "2025",
  "cash_usage_rate": 72.0,
  "cash_transaction_frequency": 65.0,
  "cash_value_share": null,
  "cash_preference_rate": 44.0,
  "source_ids": ["BCCH_ENUPE_2025"]
}
```


## `data/staging/economic_macro_context.jsonl`

```json
{
  "activity_code": "000000",
  "region_code": "13",
  "year": 2024,
  "sector_growth_yoy": 2.1,
  "region_sector_gdp_growth_yoy": 1.4,
  "credit_growth_yoy": 3.2,
  "macro_source_ids": ["SII_EMPRESAS_STATS", "BCCH_PIB_REGIONAL", "CMF_CREDIT_COMMUNE"]
}
```

## `data/staging/cash_sector_context.jsonl`

Sólo se carga si la propia fuente permite observar una categoría/sector defendible.

```json
{
  "sector_id": "UAF-SEC-14",
  "period": "2025",
  "cash_usage_rate": 80.0,
  "source_supports_sector_grain": true,
  "source_ids": ["BCCH_ENUPE_2025"]
}
```

No se construyen sectores de efectivo a partir de opiniones ni de los puntajes de vulnerabilidad de exploraciones sectoriales previas.
