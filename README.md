# Context Hub Chile · v0.1

Capa transversal de **contexto**, no un radar de hechos ni un motor de calificación AML.

Su función es responder preguntas como:

- ¿Qué exposición al flujo migratorio presenta una región o comuna, según la granularidad realmente publicada?
- ¿Qué tan inusual es el tramo de ventas, dotación o trayectoria de una sociedad frente a pares comparables?
- ¿Qué intensidad estructural de uso de efectivo caracteriza un territorio o macrozona?
- ¿Qué código territorial y sectorial común deben usar los radares para cruzarse sin depender de nombres?

## Principio rector

> Contexto ≠ sospecha ≠ evidencia de LA/FT.

Un indicador contextual puede **aumentar o disminuir la plausibilidad de una explicación**, ayudar a seleccionar comparables o priorizar revisión, pero nunca convierte por sí solo un hallazgo en conducta ilícita.

## Componentes

### 1. Territory Hub

Clave conformada:

- región: `CL-REG-{CUT_REG}`
- provincia: `CL-PROV-{CUT_PROV}`
- comuna: `CL-COM-{CUT_COM}`

La fuente canónica es CUT/Subdere; una capa DPA 2023 de IDE Chile actúa como fallback geográfico sin cambiar la clave CUT. Los nombres son atributos y los alias son gobernados; nunca se promueve fuzzy matching a verdad productiva.

La versión distribuida incluye las 16 regiones y el adaptador para materializar provincias/comunas desde CUT en una corrida con red.

### 2. Sector Hub

Contiene 55 actividades UAF y un crosswalk N:M UAF ↔ ACTECO SII.

Regla jurídica y de gobierno:

> `ACTECO SII ≠ condición de sujeto obligado UAF`.

Los códigos SII se usan para screening y enriquecimiento. Una condición regulatoria debe confirmarse con la fuente externa que corresponda.

### 3. Contexto migratorio

**No utiliza SERMIG.**

Fuentes previstas:
- Censo 2024, INE.
- Movimiento Internacional de Pasajeros, INE sobre registros de control migratorio PDI.
- Proyecciones de población INE como denominador cuando corresponda.

`migration_exposure_index_v1` mide **exposición territorial**, no riesgo AML. No utiliza nacionalidad como proxy de sospecha y no desagrega un indicador por debajo de la granularidad publicada.

### 4. Benchmark económico

El motor compara entidades contra pares usando la salida gobernada de Radar SII y estadísticas agregadas SII/BCCh/CMF/INE.

Jerarquía de pares:
1. actividad × comuna × año, si existe masa crítica;
2. actividad × región × año;
3. actividad × país × año.

No infiere ventas exactas cuando la fuente abierta sólo entrega `tramo de ventas`.

### 5. Exposición al efectivo

Usa como fuente principal la ENUPE y el Estudio Comportamiento de Pagos del Banco Central.

`cash_exposure_index_v1` expresa intensidad estructural del efectivo, **no probabilidad de LA/FT**. La geografía nunca se desagrega por debajo de la representatividad de la encuesta.

## Estructura

```text
Context-Hub/
├── config/                  políticas y catálogo de fuentes
├── src/context_hub/         motores determinísticos
├── data/bronze/             snapshots de fuente
├── data/staging/            contratos normalizados de entrada
├── data/silver/             dimensiones conformadas
├── data/gold/               contexto y estados de calidad
├── interop/                 contrato de consumo
├── docs/                    metodología y modelo
└── tests/                   guardrails
```

## Ejecución local

```bash
pip install -r requirements.txt
pytest -q
python scripts/validate.py
python scripts/run_pipeline.py
```

Primera corrida con fuente CUT disponible:

```bash
python scripts/run_pipeline.py --network
```

## Contratos de staging

La v0.1 no interpreta silenciosamente formatos externos que puedan cambiar. Las fuentes complejas pasan primero a contratos normalizados documentados en `docs/input_contracts.md`.

Eso permite que una modificación de una planilla oficial produzca un error explícito en vez de un indicador falso.

## Interoperabilidad

Context Hub no replica la base masiva de los radares. Consume y emite las mismas claves conformadas:

- `entity_id`
- `territory_id`
- `sector_id`
- `period_id`
- `source_id`

La futura capa de consulta podrá combinar hechos de los radares con contexto sin sumar scores incompatibles.
