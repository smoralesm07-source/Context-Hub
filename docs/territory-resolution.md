# Resolución territorial gobernada

Cómo un radar convierte una glosa territorial (`"Región del Biobío"`, `"O'Higgins"`, `"VIII"`) en
una clave canónica `CL-REG-*` o `CL-COM-*`.

## Por qué existe

Cada radar venía resolviendo territorio por su cuenta, o no resolviéndolo. Radar CGR mantenía una
tabla privada de 18 alias dentro de `fusion_export.py`; Context Hub publicaba 6 alias en JSONL; SII,
Presupuesto y OSFL no producían clave alguna. Ninguna de esas tablas era autoritativa y no coincidían
entre sí.

Ahora hay una sola fuente: Context Hub publica el índice y los radares lo consumen.

## Artefactos

| Artefacto | Qué es |
|---|---|
| `data/silver/dim_region.jsonl` | 16 regiones canónicas (CUT/Subdere) |
| `data/silver/dim_territory.jsonl` | 346 comunas canónicas |
| `data/seed/territory_aliases_v1.csv` | Alias gobernados, editable y revisable |
| `data/silver/territory_aliases.jsonl` | Alias materializados y validados |
| `data/gold/territory_resolution_index_v1.json` | **El índice que consumen los radares** |
| `src/context_hub/territory_resolve.py` | Resolver de referencia, con tests |
| `interop/territory_adapter_reference.py` | Adaptador de ~70 líneas para copiar en un radar |

## La receta de clave

```
NFD → eliminar diacríticos → mayúsculas → [^A-Z0-9] a espacio
    → retirar UN prefijo administrativo inicial → eliminar espacios
```

`"Región del Biobío"`, `"BIO-BÍO"` y `"Bio Bio"` colapsan a `BIOBIO`. `"O'Higgins"` colapsa a
`OHIGGINS` en vez de partirse en dos palabras, que es exactamente cómo fallaba el adaptador privado
de CGR.

## Tres reglas que no se relajan

**1. Sólo igualdad exacta.** No hay distancia de edición ni subcadenas. Lo que no cruza queda sin
resolver y se reporta como brecha. `fuzzy_match_promoted_to_truth: false` viaja en el propio índice.

**2. El nivel es obligatorio.** Siete claves existen en ambos niveles:

```
AISEN · ANTOFAGASTA · COQUIMBO · LOSLAGOS · MAULE · OHIGGINS · VALPARAISO
```

El caso peligroso es **`LOSLAGOS`**: es la Región de Los Ríos quien tiene una comuna llamada «Los
Lagos». Un índice plano de nombre a clave asignaría ese dato a la Región de Los Lagos, es decir a
otra región. Por eso el llamador declara el nivel, y `level="ANY"` devuelve `AMBIGUOUS_LEVEL` en vez
de adivinar.

**3. Un topónimo demasiado largo no es un topónimo.** El nombre canónico más largo del país tiene 35
caracteres de clave; el guardia corta en 45. Una glosa mayor se clasifica `NOT_A_PLACE_NAME`, lo que
distingue el texto arrastrado por un extractor de un nombre de lugar que simplemente falta. Esa
distinción es la que permite al Data Steward saber si debe arreglar el extractor o agregar un alias.

## Estados de resolución

| Estado | Significado | Acción |
|---|---|---|
| `VALIDATED_EXACT` | Cruzó contra nombre canónico o alias gobernado | ninguna |
| `CODE_EXACT` | La fuente ya traía el código CUT | ninguna |
| `UNRESOLVED_NAME_ONLY` | Glosa plausible sin equivalencia | evaluar alias gobernado |
| `NOT_A_PLACE_NAME` | Texto arrastrado por el extractor | arreglar la extracción aguas arriba |
| `UNKNOWN` | La fuente no trae territorio | nada que resolver |
| `AMBIGUOUS_LEVEL` | La glosa existe en dos niveles | declarar el nivel |

## Integrar un radar

1. Copiar `data/gold/territory_resolution_index_v1.json` a `config/` del radar.
2. Copiar `interop/territory_adapter_reference.py` como `<paquete>/territory.py` y ajustar
   `INDEX_PATH`.
3. Llamar `resolve(glosa, "REGION")` o `resolve(glosa, "COMMUNE")` donde el radar produce su
   registro de fusión, y escribir `territory_id` y `territory_mapping_status`.
4. Medir la tasa real sobre los datos del radar y publicarla en
   `interop/integration_manifest_v1.json` bajo `territory.measured`. El cockpit prefiere esa cifra
   medida por sobre la etapa cualitativa del manifiesto.
5. Agregar tests con las glosas reales que el radar observa, incluidas las que **no** deben resolver.

## Estado por radar

| Radar | Estado | Resolución medida |
|---|---|---|
| CGR | integrado y medido | 97,3% de filas · 22 de 24 glosas distintas |
| Delictual | ya usaba códigos CUT | `CODE_EXACT` nativo |
| Context Hub | fuente canónica | — |
| SII | pendiente | sin datos en el repositorio para medir |
| Presupuesto | pendiente | sin datos en el repositorio para medir |
| OSFL | pendiente | sin datos en el repositorio para medir |
| UAF, Sanciones | territorio no es dimensión primaria | no aplica |

Las dos glosas que CGR no resuelve son artefactos de extracción
(`", oficina del SAG a cargo,"` y un párrafo con «Documento Asociado Descargar documento»), no
topónimos faltantes. Se rechazan a propósito.
