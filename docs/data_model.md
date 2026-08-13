# Modelo de datos

## Dimensiones conformadas

### `dim_territory`

Grano: un territorio administrativo.

Campos principales:
`territory_id`, `territory_level`, `region_code`, `province_code`, `commune_code`,
`canonical_name`, `source_system`, `mapping_method`, `mapping_confidence`.

### `dim_sector`

Grano: una actividad/sector de la taxonomía UAF.

No contiene el puntaje de riesgo de exploraciones sectoriales previas. Su finalidad es taxonómica.

### `sector_sii_mapping_v1`

Grano: una relación UAF-sector ↔ ACTECO SII.

Estados:
- `VALIDATED_EXACT`
- `VALIDATED_RULE`
- `EMPIRICAL_CANDIDATE`
- `AMBIGUOUS`
- `NO_EQUIVALENCE`

En v0.1 los matches directos del crosswalk previo se modelan como `VALIDATED_RULE`:
el código es una regla fuerte de preselección, pero la condición regulatoria exige validación externa.

## Hechos contextuales

### `migration_context_v1`
Grano recomendado: territorio × período × granularidad de la fuente.

### `economic_peer_context_v1`
Grano: entidad × año, enriquecida con benchmark de pares.

### `cash_context_v1`
Grano: geografía representativa × período de encuesta.

Nunca mezclar filas de granos distintos en una única tabla central.
