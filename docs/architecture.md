# Arquitectura

```text
RADARES (hechos / señales)                  CONTEXT HUB (explica / compara)
─────────────────────────                  ───────────────────────────────
Radar-CGR                                  Migración territorial
Radar_SII ───── entity_id ───────┐         Benchmark económico
Radar_UAF                        │         Exposición al efectivo
Presupuesto                      │         Contexto financiero
Sanciones                        │
Delictual ─ territory_id ────────┼──── Territory Hub
                                 ├──── Sector Hub
                                 └──── Source / Period dimensions
```

## Separación de responsabilidades

- **Radar:** descubre, estructura o prioriza un hecho.
- **Context Hub:** sitúa ese hecho frente a su entorno.
- **Entity Hub:** resuelve quién es la entidad.
- **Territory Hub:** resuelve dónde.
- **Sector Hub:** resuelve qué taxonomía económica/regulatoria corresponde y con qué nivel de certeza.
- **Futura capa de consulta:** combina sin borrar origen, grano ni evidencia.

No existe un `risk_score` global en Context Hub.
