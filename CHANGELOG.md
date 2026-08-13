# Changelog

## 0.1.0 — 2026-08-13
- crea Context Hub como componente separado de los radares;
- Territory Hub con claves CUT, semilla regional y adaptadores Subdere/DPA;
- Sector Hub con 55 sectores y 74 relaciones gobernadas UAF↔SII;
- excluye SERMIG del componente migratorio;
- crea `migration_exposure_index_v1` como exposición contextual, no AML;
- crea benchmark económico por pares usando tramos SII y contexto macro opcional;
- crea exposición al efectivo territorial y sectorial sólo cuando la fuente soporta el grano;
- incorpora preservación de último dato válido y política `missing != zero`;
- incorpora CI, validación y refresh semanal.
