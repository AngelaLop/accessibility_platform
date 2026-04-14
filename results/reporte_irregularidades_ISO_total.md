# Reporte de Irregularidades — Archivos `ISO_total`
**Proyecto:** Plataforma de Accesibilidad Escolar — IDB/BID  
**Fecha:** 2026-03-23  
**Preparado por:** Equipo de datos  
**Cobertura:** 21 países de América Latina y el Caribe

---

## Contexto

El BID solicitó originalmente un directorio de **escuelas públicas K-12** (primaria y secundaria) para 21 países de la región. Para cada país existe un archivo `{ISO}_total.csv` y `{ISO}_total.geojson` generado por un script R/Quarto a partir de los datos crudos del ministerio de educación correspondiente.

Durante la auditoría de estos archivos se identificaron irregularidades que afectan la consistencia del dataset regional. Este reporte las documenta por orden de severidad.

---

## I. Irregularidades sobre sector público/privado

> **Relevancia directa para el mandato del BID**, que solicitó exclusivamente escuelas públicas.

### 1.1 Ningún archivo `ISO_total` indica explícitamente qué sector incluye

**Afecta: los 21 países**

La función `procesar_datos()` del pipeline en R **no exporta ninguna columna de sector** al archivo de salida (`ISO_total.csv` / `ISO_total.geojson`). Esto significa que un usuario que abre cualquiera de estos archivos no puede determinar si está mirando escuelas públicas, privadas, o ambas — sin consultar el script original y el archivo crudo.

---

### 1.2 Dieciocho países contienen únicamente escuelas públicas, pero no lo declaran

Los scripts QMD de 18 países aplican un filtro de sector explícito que excluye las escuelas privadas. El resultado son archivos de escuelas públicas que se presentan bajo el nombre genérico `ISO_total`, sin ninguna advertencia sobre el alcance real.

| ISO | País | Filtro aplicado en el QMD |
|-----|------|---------------------------|
| ARG | Argentina | `sector == 1` (1 = Público) |
| BLZ | Belize | Solo fuente de gobierno disponible |
| BOL | Bolivia | `dependencia != "Privada"` |
| BRA | Brasil | `TP_DEPENDENCIA %in% c(1,2,3)` (federal/estadual/municipal) |
| CHL | Chile | `cod_depe != 4` vía sistema SAE |
| COL | Colombia | `sector_id == 1` (Oficial) |
| CRI | Costa Rica | `DEPENDENCIA == "PUB"` |
| DOM | R. Dominicana | Filtro de año que excluía privadas |
| ECU | Ecuador | `sostenimiento != "Particular"` |
| GTM | Guatemala | SIRE registra principalmente escuelas MINEDUC |
| HND | Honduras | SIPLIE es sistema del gobierno |
| MEX | México | `control == "PÚBLICO"` |
| PAN | Panamá | `dependencia == "OFICIAL"` |
| PER | Perú | `d_gestion != "Privada"` |
| PRY | Paraguay | `sector_o_tipo_gestion != "Privado"` |
| SUR | Suriname | Mayoritariamente público (ver 1.3) |
| URY | Uruguay | Fuente ANEP (sistema público exclusivo) |
| GUY | Guyana | Sistema National/Community (público) |

**Implicación:** estos archivos cumplen con el mandato del BID (escuelas públicas), pero la ausencia de documentación interna en el archivo genera riesgo de uso incorrecto por terceros.

---

### 1.3 Un país mezcla públicas y privadas de forma explícita: SLV ⚠

**Afecta: El Salvador**  
**Severidad: Alta**

En la versión activa del script `SLV_script.qmd` el filtro de sector **está comentado**. Existe evidencia de que el archivo fuente (`CE_2024 El Salvador.xlsx`) contiene escuelas privadas: el archivo de coordenadas `SLV_coord_EDU.csv` registra 5,143 públicas y 883 privadas (total 6,026).

Si el `CE_2024` incluye privadas, el `SLV_total` procesado puede contener hasta **883 establecimientos privados no identificados** mezclados con los públicos, sin ninguna columna que permita separarlos.

**Acción requerida:** verificar el contenido de `CE_2024 El Salvador.xlsx` y, si contiene privadas, reactivar el filtro de sector o reconstruir el archivo con etiqueta explícita.

---

### 1.4 Un país mezcla una cantidad marginal de privadas: SUR ⚠

**Afecta: Suriname**  
**Severidad: Baja**

El archivo fuente `Suriname School List_03202024.xlsx` contiene aproximadamente **5 escuelas del tipo `"Particulier"`** (privadas). El CSV procesado no tiene columna de tipo de institución, por lo que no es posible identificarlas o excluirlas sin volver al archivo crudo. Representan menos del 1% del total (547 registros).

**Acción requerida:** verificar si el mandato requiere excluirlas; si sí, filtrar en el QMD y añadir la columna de sector al output.

---

### 1.5 Tres países con sector indeterminado ⚠

Para estos países no es posible determinar si el `ISO_total` contiene escuelas públicas, privadas, o ambas:

| ISO | País | Motivo |
|-----|------|--------|
| **BRB** | Barbados | El archivo fuente no tiene columna de sector. Se desconoce la naturaleza de las 106 escuelas incluidas. |
| **JAM** | Jamaica | El script QMD es un archivo vacío (placeholder). No hay datos crudos en el repositorio. El origen del `JAM_total` es completamente desconocido. |
| **BHS** | Bahamas | Solo existe un dataset de Puntos de Interés (POI shapefile) sin información de sector ni nivel educativo. |

**Acción requerida:** para BRB, contactar al ministerio para obtener metadatos de sector. Para JAM y BHS, documentar el origen de los datos y reconstruir el pipeline desde fuentes ministeriales.

---

## II. Otras irregularidades identificadas

### 2.1 Filas duplicadas en ISO_total de Perú 🔴

**Afecta: Perú (PER)**  
**Severidad: Alta — infla el conteo de escuelas**

El archivo `PER_total.csv` contiene **3,879 filas con `id_centro` duplicado** (mismo identificador, mismas coordenadas). El conteo real de escuelas únicas es **65,263**, no 69,142 como indica el archivo.

| Métrica | Valor |
|---|---:|
| Filas en ISO_total | 69,142 |
| Filas duplicadas exactas | 3,071 |
| Filas con `id_centro` repetido | 3,879 |
| **Escuelas únicas reales** | **65,263** |
| Inflación del conteo | **+5.9%** |

**Causa raíz:** el QMD de PER realiza múltiples joins entre el padrón de instituciones y los archivos de matrícula/recursos por `cod_mod`. Cuando una escuela aparece en más de una fuente con el mismo código, el join genera filas duplicadas que `procesar_datos()` no deduplica antes de exportar.

**Nota:** el bug fue identificado en los quality checks del propio QMD (`"Bug confirmado: 2,416 escuelas con duplicados. Denominador incorrecto: 82,019 cod_mod vs. 69,957 locales únicos [ESCALE]"`), pero no fue corregido en el archivo exportado.

**El CIMA no tiene este problema:** el script Python agrega por `id_centro` durante la construcción, eliminando los duplicados automáticamente. `PER_total_cima.csv` tiene 53,342 filas sin ningún `id_centro` duplicado.

**Acción requerida:** corregir el QMD de PER para deduplicar por `id_centro` antes de llamar a `procesar_datos()` y regenerar `PER_total.csv` y `PER_total.geojson`.

---

### 2.2 Archivos CSV corruptos — pérdida real de datos 🔴

Dos países tienen archivos `CSV` con celdas corruptas que contienen saltos de línea embebidos, causando pérdida masiva de registros al leer el archivo:

| ISO | Filas GeoJSON (correcto) | Filas CSV (corrompido) | Filas perdidas | % pérdida |
|-----|-------------------------:|----------------------:|---------------:|----------:|
| **ECU** | 12,767 | 6,382 | **6,385** | **50%** |
| **ARG** | 37,857 | 35,636 | **2,221** | **6%** |

El GeoJSON es la fuente de verdad en ambos casos. El CSV debe ser regenerado corriendo el script QMD correspondiente.

---

### 2.2 Definición de K-12 inconsistente entre países 🟠

El `ISO_total` no aplica un criterio uniforme sobre qué niveles educativos incluir. Varios países incluyen **nivel inicial (preescolar/parvularia)**, lo que infla el conteo de instituciones más allá del mandato K-12 (primaria + secundaria):

| ISO | País | Estimado de escuelas de nivel inicial incluidas |
|-----|------|------------------------------------------------:|
| MEX | México | ~49,000 |
| PER | Perú | ~29,000 |
| ARG | Argentina | ~9,900 |
| BRA | Brasil | ~4,442 |
| GTM | Guatemala | ~623 |
| PRY | Paraguay | ~534 |
| GUY | Guyana | ~328 (guarderías) |
| HND | Honduras | ~29 (Pre-Básica) |
| BLZ | Belize | ~30 |

---

### 2.3 Pipeline no documentado ni reproducible 🟠

**Afecta: Jamaica (JAM)**

El archivo `JAM_script.qmd` contiene únicamente el contenido de plantilla (`1 + 1`, `2 * 2`). No existe ningún script de procesamiento real. No hay datos crudos en la carpeta `raw/`. El archivo `JAM_total` existe pero no puede auditarse, verificarse ni regenerarse.

---

### 2.4 Variables faltantes en el output exportado 🟡

| ISO | Variable faltante | Impacto operativo |
|-----|-------------------|-------------------|
| **GUY** | `nivel_primaria`, `nivel_secbaja`, `nivel_secalta` | No es posible filtrar K-12 del dataset. El archivo CIMA no pudo generarse. |
| **BRB** | `latitud`, `longitud` en el CSV | El GeoJSON sí contiene geometrías. La función `procesar_datos()` no las exportó al CSV. |

---

### 2.5 Datos desactualizados o desincronizados 🟡

| ISO | Problema | Detalle |
|-----|----------|---------|
| **DOM** | Año incorrecto | Se usa período 2022-2023. La misma fuente contiene datos 2023-2024 con 7,893 escuelas (+1,294 sobre las actuales 6,599). El script aplica `filter(ano == 20222023)`. |
| **MEX** | Desincronización CSV/GeoJSON | El GeoJSON tiene **227 features más** que el CSV. Los archivos fueron generados en ejecuciones distintas del script. |

---

### 2.6 Chile: 15 escuelas técnicas excluidas por error de definición 🟢

El filtro K-12 del script de Chile no incluye los códigos de enseñanza `710` (Media TP Técnica), `810` (Media TP Administración) y `910` (Media TP Servicios), que sí corresponden a 1°–4° Medio y sí estaban en el script QMD original. Hay **15 escuelas** que ofrecen únicamente estas modalidades y quedan excluidas del dataset actual. Corrección pendiente en `_build_cima_v2.py`.

---

## III. Resumen ejecutivo

| # | Irregularidad | Severidad | Países afectados |
|---|---------------|-----------|------------------|
| 1 | Ningún archivo indica qué sector incluye (sin columna de sector) | 🔴 Transversal | **21 países** |
| 2 | 18 países contienen solo escuelas públicas sin declararlo | 🟠 Riesgo de uso incorrecto | ARG, BLZ, BOL, BRA, CHL, COL, CRI, DOM, ECU, GTM, GUY, HND, MEX, PAN, PER, PRY, SUR, URY |
| 3 | SLV puede mezclar hasta 883 escuelas privadas sin identificar | 🔴 Alto | SLV |
| 4 | SUR mezcla ~5 escuelas privadas sin identificar | 🟢 Bajo | SUR |
| 5 | BRB, JAM, BHS: sector completamente indeterminado | 🟠 Alto | BRB, JAM, BHS |
| 6 | CSV corruptos con pérdida real de registros | 🔴 Crítico | ARG (−2,221), ECU (−6,385) |
| 7 | **Filas duplicadas — conteo inflado en 3,879 escuelas** | 🔴 Alto | **PER** |
| 8 | Nivel inicial incluido en K-12 (inflación de conteos) | 🟠 Medio | MEX, PER, ARG, BRA, GTM, PRY, GUY, HND, BLZ |
| 9 | Pipeline sin documentar ni reproducir | 🟠 Medio | JAM |
| 10 | Variables de nivel/coordenadas faltantes en output | 🟡 Medio | GUY, BRB |
| 11 | Datos desactualizados / desincronizados | 🟡 Bajo | DOM, MEX |
| 12 | 15 escuelas técnicas excluidas (CHL) | 🟢 Mínimo | CHL |

---

## IV. Acciones recomendadas

### Prioridad inmediata
1. **Regenerar ECU_total.csv** — pierde el 50% de las escuelas. Correr `ECU_script.qmd`.
2. **Regenerar ARG_total.csv** — pierde 2,221 filas. Correr `ARG_script.qmd`.
3. **Corregir PER_total** — 3,879 filas duplicadas inflan el conteo de 65,263 a 69,142. Deduplicar por `id_centro` en `PER_script.qmd` antes de `procesar_datos()`.
3. **Verificar SLV** — confirmar si `CE_2024 El Salvador.xlsx` contiene privadas y aplicar filtro.

### Prioridad corto plazo
4. **Agregar columna `sector`** al output de `procesar_datos()` para todos los países — actualmente ningún archivo lo indica.
5. **Estandarizar definición K-12** — excluir nivel inicial de todos los países que actualmente lo incluyen.
6. **Resolver GUY** — agregar columnas `nivel_` al output del script.
7. **Sincronizar MEX** — volver a correr el script para igualar CSV y GeoJSON.

### Prioridad mediano plazo
8. **Documentar JAM** — construir script de procesamiento y obtener datos crudos del ministerio.
9. **Actualizar DOM** — usar datos 2023-2024 disponibles en la misma fuente.
10. **Clarificar BRB** — confirmar sector de las 106 escuelas con el ministerio.
11. **Corregir CHL** — agregar `cod_ense` 710/810/910 al filtro K-12 (15 escuelas).

---

*Este reporte fue generado a partir de la auditoría automatizada de scripts QMD y archivos procesados realizada el 2026-03-23. El archivo CIMA (`{ISO}_total_cima.csv`) corrige la mayoría de estas irregularidades: incluye la columna `sector`, filtra estrictamente K-12, e incorpora escuelas privadas desde los archivos crudos de cada ministerio.*
