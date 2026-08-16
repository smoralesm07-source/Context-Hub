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

**2. El nivel es obligatorio.** Hay tres niveles indexados —`REGION` (41 claves), `PROVINCE` (56) y
`COMMUNE` (346)— y **34 claves existen en más de uno**. 28 nombres de provincia son además nombres
de comuna, y 3 son además nombres de región.

El caso peligroso es **`LOSLAGOS`**: es la Región de Los Ríos quien tiene una comuna llamada «Los
Lagos». Un índice plano de nombre a clave asignaría ese dato a la Región de Los Lagos, es decir a
otra región. Por eso el llamador declara el nivel, y `level="ANY"` devuelve `AMBIGUOUS_LEVEL` en vez
de adivinar.

**2b. Una glosa compuesta debe concordar consigo misma.** El SII publica la región como
`XIII REGION METROPOLITANA`: numeral romano y nombre en un mismo campo. Son dos señales
independientes, así que se resuelven por separado y se exige que apunten al mismo lugar. Si
discrepan —`IV REGION METROPOLITANA`— el resultado es `CONFLICTING_SIGNALS`, no una de las dos.

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
| `AMBIGUOUS_LEVEL` | La glosa existe en más de un nivel | declarar el nivel |
| `CONFLICTING_SIGNALS` | Numeral y nombre de una glosa compuesta discrepan | revisar el dato de origen |

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
| SII | integrado, tres niveles | 100% sobre la muestra provista (5 filas) |
| CGR | integrado y medido | 97,3% de filas · 22 de 24 glosas distintas |
| Delictual | ya usaba códigos CUT | `CODE_EXACT` nativo |
| Context Hub | fuente canónica | — |
| Presupuesto | pendiente | sin datos en el repositorio para medir |
| OSFL | pendiente | sin datos en el repositorio para medir |
| UAF, Sanciones | territorio no es dimensión primaria | no aplica |

Las dos glosas que CGR no resuelve son artefactos de extracción
(`", oficina del SAG a cargo,"` y un párrafo con «Documento Asociado Descargar documento»), no
topónimos faltantes. Se rechazan a propósito.


## Deriva entre el hub y las copias vendorizadas

Los radares copian el adaptador en vez de importar `context_hub`, así que la deriva entre ambas
implementaciones es el riesgo real de ese diseño.
`test_reference_adapter_agrees_with_the_hub` compara las dos sobre un corpus de 25 glosas y exige
que el `territory_id` coincida siempre.

El vocabulario de estados del adaptador es deliberadamente más grueso: el índice exportado aplana
nombre canónico y alias en un solo mapa, de modo que no puede distinguir `VALIDATED_ALIAS` de
`VALIDATED_EXACT`. Lo que nunca puede diferir es la clave, que es lo que entra a la capa de fusión.

## Coherencia entre niveles

Cuando una fuente publica región y comuna a la vez —como el SII— las dos claves se cruzan: el
código CUT de comuna lleva la región en sus dos primeros dígitos. Una fila cuya comuna no pertenece
a la región declarada se marca `REGION_COMMUNE_MISMATCH`.

Ninguna de las dos claves se descarta ni se ajusta: el defecto es del dato de origen y corregirlo
en silencio ocultaría un problema de calidad aguas arriba.
