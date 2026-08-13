# Benchmark económico v1

## Pregunta analítica

¿Una empresa se comporta de forma inusual frente a entidades comparables por actividad, geografía y período?

## Variables objetivo

- tramo de ventas SII;
- trabajadores;
- antigüedad;
- actividad económica;
- territorio;
- cambio de tramo;
- tendencia del sector;
- PIB regional por actividad;
- contexto crediticio CMF cuando exista.

## Jerarquía de pares

Se utiliza el nivel más específico con al menos 20 pares:
1. ACTECO × comuna × año;
2. ACTECO × región × año;
3. ACTECO × país × año.

Si ni siquiera el grupo nacional alcanza el mínimo, el contexto se conserva con `peer_group_sufficient=false`.

## Variables derivadas

- `sales_band_percentile`
- `workers_percentile`
- `company_age_percentile`
- `sales_worker_gap`
- `company_sales_band_delta_1y`
- `economic_divergence_index_v1`

El índice de divergencia es explicativo y de priorización contextual. No es probabilidad de delito ni score AML.

## Limitación SII

Cuando la nómina abierta entrega un tramo de ventas, Context Hub usa **el tramo**, no inventa un monto exacto.
