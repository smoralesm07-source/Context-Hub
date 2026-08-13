# Contexto migratorio v1

## Propósito

Responder **qué tan expuesto está un territorio a dinámicas migratorias observables**.

No responde si el territorio es riesgoso para LA/FT.

## Fuentes permitidas en esta versión

1. INE — Censo 2024, inmigración internacional.
2. INE — Movimiento Internacional de Pasajeros, sobre registros de control migratorio PDI.
3. INE — proyecciones de población, cuando se necesitan denominadores.

**SERMIG está deliberadamente excluido de esta versión.**

## Índice

Pesos máximos:

- 50% percentil de participación de residentes nacidos/extranjeros según la variable publicada y metodológicamente pertinente;
- 35% intensidad de movimientos internacionales por población;
- 15% variación migratoria comparable en el tiempo, sólo si existe una serie compatible.

Los pesos se renormalizan sobre componentes disponibles. Una fuente ausente no vale cero.

## Guardrails

- Nacionalidad no se transforma en puntaje AML.
- No se imputa movimiento de un control fronterizo a una comuna sin base geográfica.
- No se distribuye un dato regional entre comunas.
- Se publica `score_coverage` junto con cualquier índice.
