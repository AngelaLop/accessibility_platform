# Bitácora de Errores del Pipeline de Datos Escolares LAC
**Proyecto:** Plataforma de Accesibilidad Escolar — IDB  
**Fecha de revisión:** 2026-03-23  
**Cobertura:** 21 países de América Latina y el Caribe  
**Autor del análisis:** Revisión automatizada + revisión de scripts R/Quarto

---

## Cómo funciona el pipeline

Para cada país existe:
1. **Datos crudos** (`raw/`): archivo(s) del ministerio de educación
2. **Script R/Quarto** (`{ISO}_script.qmd`): filtra, limpia y estandariza las variables
3. **Archivo procesado** (`processed/{ISO}_total.csv` y `processed/{ISO}_total.geojson`): salida del pipeline

El script R llama a la función `procesar_datos()` (definida en `funciones.R`) que genera simultáneamente el CSV y el GeoJSON. Si los dos archivos tienen el mismo número de filas/features, el pipeline está íntegro.

---

## Resumen ejecutivo de errores

| Severidad | Descripción | Países afectados |
|-----------|-------------|------------------|
| 🔴 CRÍTICO | CSV corrupto (datos perdidos, archivo debe regenerarse) | ARG, ECU |
| 🟠 ALTO | CSV y GeoJSON desincronizados (conteos distintos) | ARG, ECU, MEX |
| 🟡 MEDIO | Script R es placeholder vacío (sin pipeline documentado) | JAM |
| 🟡 MEDIO | No hay columnas de nivel educativo en CSV procesado | GUY |
| 🟡 MEDIO | Filtro de sector privado comentado — puede incluir privados | SLV |
| 🟡 MEDIO | Sin columnas de coordenadas en CSV procesado | BRB |
| 🟢 INFO | Incluye escuelas privadas o subvencionadas sin poder distinguirlas | SLV, SUR, CHL |
| 🟢 INFO | Datos más antiguos que el resto de la región | DOM (2022-23) |

---

## Detalle por país

---

### 🔴 ARG — Argentina

**Fuente:** Listado de Establecimientos 2023, Ministerio de Educación  
**Año de datos:** 2023  
**Universo esperado (ministerio):** 45,000 establecimientos principales de educación regular (sector público + privado + cooperativa)

#### Pipeline
| Paso | Filtro aplicado | Filas resultantes |
|------|----------------|------------------|
| Raw | Total en archivo | 64,582 |
| Paso 1 | `sector == 1` (público) | 51,885 |
| Paso 2 | `comun == 'X'` (educación regular) | 39,467 |
| Paso 3 | Al menos un nivel K-12 | 37,857 |
| **GeoJSON** | Salida correcta del R | **37,857** |
| **CSV (pandas)** | Salida corrupta | **35,636** |

#### Errores detectados

**[ARG-ERR-1] 🔴 CRÍTICO: CSV corrupto**  
El archivo `ARG_total.csv` tiene una celda en la fila 29,574, columna `nivel_inicial`, que contiene **178,469 caracteres** con **2,928 saltos de línea embebidos**. Esto ocurrió al escribir el CSV: una comilla de cierre faltante causó que 1,464 filas se concatenaran dentro de esa celda.

- Pandas lee: **35,636 filas** (colapsa las 1,464 filas embebidas en una sola)
- Conteo de líneas crudas: **37,105** (infla el conteo por los saltos embebidos)
- Excel lee: **~36,816** (recuperación parcial del campo corrupto)
- **Ninguno de estos números es correcto.** El archivo debe regenerarse.

**[ARG-ERR-2] 🟠 ALTO: CSV y GeoJSON desincronizados**  
- GeoJSON: **37,857** features (correcto)
- CSV (pandas): **35,636** filas (incorrecto por corrupción)
- Diferencia: **2,221 filas** perdidas en el CSV

**Acción requerida:** Volver a correr `ARG_script.qmd` y regenerar el CSV. El GeoJSON es la fuente de verdad.

---

### ✅ BLZ — Belize

**Fuente:** `geo_schools Belize.xlsx`  
**Año de datos:** 2024  
**Sector:** Gobierno + Gobierno Asistido + Especialmente Asistido (sin escuelas privadas en el archivo)

- CSV: **303 filas** | GeoJSON: **303 features** ✅ sincronizados
- Georeferenciadas: **303 (100%)**
- Sin errores críticos detectados.

**[BLZ-INFO-1]** El archivo fuente no contiene escuelas privadas, por lo que no es posible comparar cobertura frente al universo total (público + privado).

---

### ✅ BOL — Bolivia

**Fuente:** `MinEdu_InstitucionesEducativas_2023.xlsx`  
**Año de datos:** 2023  
**Sector:** Fiscal + Convenio + Comunitaria (excluye Privada)

- CSV: **15,329 filas** | GeoJSON: **15,329 features** ✅ sincronizados
- Georeferenciadas: **15,299 (99.8%)**
- Sin errores críticos detectados.

---

### ✅ BRA — Brasil

**Fuente:** Microdatos Censo Escolar INEP 2023 + GeoBR  
**Año de datos:** 2023  
**Sector:** Dependencia federal + estadual + municipal (excluye privadas)

- CSV: **134,418 filas** | GeoJSON: **134,418 features** ✅ sincronizados
- Georeferenciadas: **116,542 (86.7%)** — el mayor déficit de georeferenciación en la región

**[BRA-INFO-1]** 17,876 escuelas públicas brasileñas no tienen coordenadas en el Censo Escolar 2023. Esto representa el 13.3% del total. Para estas escuelas, las opciones son: (a) buscar coordenadas por dirección (disponible en el campo `address`), o (b) asignar centroide del municipio.

---

### 🟡 BRB — Barbados

**Fuente:** `Barbados Geolocalización Escuelas 2024.xlsx`  
**Año de datos:** 2024  
**Sector:** Desconocido (no hay columna de sector en los datos crudos)

- CSV: **106 filas** | GeoJSON: **106 features** ✅ sincronizados
- Georeferenciadas: **0** — el CSV procesado **no tiene columnas de latitud/longitud**

**[BRB-ERR-1] 🟠 ALTO: Sin coordenadas en CSV procesado**  
El archivo procesado `BRB_total.csv` no tiene columnas `latitud` ni `longitud`. El GeoJSON sí contiene geometrías (106 features con geometría), lo que sugiere que la función `procesar_datos()` en R no exportó las coordenadas al CSV correctamente.

**[BRB-ERR-2] 🟡 MEDIO: Sin dirección disponible**  
Los datos crudos de Barbados no contienen dirección de los establecimientos. Si se necesita georeferenciar las escuelas faltantes, no hay fallback de dirección disponible.

---

### ✅ CHL — Chile

**Fuente:** Directorio Oficial EE 2023 + SAE + Matrícula  
**Año de datos:** 2023  
**Sector:** Municipal + Particular Subvencionado + SLE (excluye Corp. Delegada)

- CSV: **7,895 filas** | GeoJSON: **7,895 features** ✅ sincronizados
- Georeferenciadas: **7,895 (100%)**
- Sin errores críticos detectados.

**[CHL-INFO-1]** El dataset incluye escuelas **Particular Subvencionado** (privadas financiadas por el Estado). No hay columna de sector en el CSV procesado, por lo que no es posible separar municipales de subvencionadas sin volver al archivo crudo. En el archivo CIMA se etiquetan todas como "Public" (son de financiamiento público).

---

### ✅ COL — Colombia

**Fuente:** DANE C600 2023  
**Año de datos:** 2023  
**Sector:** Sector oficial (público) únicamente

- CSV: **43,658 filas** | GeoJSON: **43,658 features** ✅ sincronizados
- Georeferenciadas: **43,259 (99.1%)**
- Sin errores críticos detectados.

**[COL-INFO-1]** Las coordenadas provienen de dos fuentes (SISE-DANE y un archivo adicional CE). En caso de conflicto, se usa la coordenada de DANE. Para las 399 escuelas sin coordenadas, existe el campo `direccion` disponible en los datos crudos.

---

### 🟡 CRI — Costa Rica

**Fuente:** Nómina de Centros Educativos 2024 (MEP)  
**Año de datos:** 2024  
**Sector:** Público (dependencia == "PUB")

- CSV: **4,418 filas** | GeoJSON: **4,418 features** ✅ sincronizados
- Georeferenciadas: **4,381 (99.2%)**

**[CRI-INFO-1]** El script de CRI fue parcialmente refactorizado (hay código comentado de la versión anterior) y la función `procesar_datos()` está comentada en el bloque principal. El archivo procesado puede corresponder a una versión anterior del script. Se recomienda verificar que el script actual produce el mismo resultado.

---

### 🟡 DOM — República Dominicana

**Fuente:** Centros Educativos Período Escolar 2022-2023  
**Año de datos:** 2022 (más antiguo que todos los demás países en la región)  
**Sector:** Público + Semioficial (excluye Privado)

- CSV: **6,599 filas** | GeoJSON: **6,599 features** ✅ sincronizados
- Georeferenciadas: **6,294 (95.4%)**

**[DOM-INFO-1]** Los datos son del año escolar 2022-2023, mientras que el archivo fuente también contiene datos de 2023-2024 (7,893 escuelas). Se recomienda actualizar al período más reciente. El script aplica `filter(ano==20222023)`.

**[DOM-INFO-2]** 305 escuelas sin coordenadas. No hay campo de dirección disponible en el CSV procesado para estas escuelas.

---

### 🔴 ECU — Ecuador

**Fuente:** MINEDUC Registros Administrativos 2024-2025 + Shapefile AMIE  
**Año de datos:** 2024  
**Sector:** No Particular (Fiscal + Fiscomisional + Municipal)

#### Pipeline
| Paso | Registros |
|------|-----------|
| Registros administrativos (filtrado) | 12,767 |
| **GeoJSON** (correcto) | **12,767** |
| **CSV (pandas)** (corrupto) | **6,382** |

#### Errores detectados

**[ECU-ERR-1] 🔴 CRÍTICO: CSV gravemente corrupto**  
El archivo `ECU_total.csv` tiene una celda con **891,985 caracteres** y **12,330 saltos de línea embebidos**. Es el caso más grave del repositorio: **6,385 filas están perdidas** (más de la mitad del total).

**[ECU-ERR-2] 🟠 ALTO: CSV y GeoJSON gravemente desincronizados**  
- GeoJSON: **12,767 features** (correcto)
- CSV (pandas): **6,382 filas** (pierde el 50% de las escuelas)
- Diferencia: **6,385 filas**

**Acción requerida:** Regenerar urgentemente `ECU_total.csv` corriendo `ECU_script.qmd`. El GeoJSON es la fuente de verdad.

---

### ✅ GTM — Guatemala

**Fuente:** SIRE 2024 (shapefile filtrado)  
**Año de datos:** 2024  
**Sector:** Oficial + Cooperativa + Municipal (excluye Privado)

- CSV: **35,973 filas** | GeoJSON: **35,973 features** ✅ sincronizados
- Georeferenciadas: **35,973 (100%)**
- Sin errores críticos detectados.

---

### 🟡 GUY — Guyana

**Fuente:** `School Data-Mapping.xlsx` + `Updated Teachers information by level.xlsx`  
**Año de datos:** 2024  
**Sector:** Gobierno (sin escuelas privadas en los datos)

- CSV: **874 filas** | GeoJSON: **874 features** ✅ sincronizados
- Georeferenciadas: **874 (100%)**

**[GUY-ERR-1] 🟡 MEDIO: Sin columnas de nivel educativo en el CSV procesado**  
El CSV de Guyana no contiene las columnas `nivel_inicial`, `nivel_primaria`, `nivel_secbaja` ni `nivel_secalta`. Las columnas de nivel se generan en el script a partir del archivo de docentes (`Updated Teachers information by level.xlsx`), pero parece que no se incluyeron en la exportación final. **No fue posible generar el archivo CIMA para Guyana.**

**Acción requerida:** Revisar la función `procesar_datos()` para Guyana y asegurarse de que las columnas de nivel se incluyen en el output exportado.

---

### 🟡 HND — Honduras

**Fuente:** SIPLIE Nacional 2023 (`SIPLIE_nivel nacional.xlsx`)  
**Año de datos:** 2023  
**Sector:** Público (SIPLIE es el sistema de información del gobierno, no incluye privados)

- CSV: **16,955 filas** | GeoJSON: **16,955 features** ✅ sincronizados
- Georeferenciadas: **16,234 (95.7%)**

**[HND-INFO-1]** 721 escuelas sin coordenadas. El campo `direccion_centro` está disponible en los datos crudos y puede usarse para geocodificación.

---

### 🟡 JAM — Jamaica

**Fuente:** Desconocida  
**Año de datos:** 2024 (estimado)  
**Sector:** Desconocido

- CSV: **955 filas** | GeoJSON: **955 features** ✅ sincronizados
- Georeferenciadas: **953 (99.8%)**

**[JAM-ERR-1] 🟡 MEDIO: Script R es un placeholder vacío**  
El archivo `JAM_script.qmd` contiene únicamente el texto de plantilla de Quarto (`1 + 1`, `2 * 2`). No existe pipeline documentado para Jamaica. El archivo procesado fue generado por algún proceso anterior no documentado en el repositorio.

**Implicaciones:**
- No es posible auditar cómo se generaron los archivos.
- No hay archivo de datos crudos en `raw/`.
- No hay información de sector (público/privado).
- No se puede regenerar el archivo si se corrompe o actualiza.

**Acción requerida:** Documentar el origen de los datos y construir el script de procesamiento. El universo estimado para Jamaica es ~1,050-1,200 escuelas totales.

---

### 🟠 MEX — México

**Fuente:** SIGED (Sistema de Información de Gestión Educativa)  
**Año de datos:** 2024  
**Sector:** Público (control == "PÚBLICO")

- CSV: **205,848 filas** | GeoJSON: **206,075 features**
- Diferencia: **227 features** (GeoJSON tiene más)
- Georeferenciadas: **205,848 (100%)**

**[MEX-ERR-1] 🟠 ALTO: CSV y GeoJSON levemente desincronizados**  
El GeoJSON tiene 227 features más que el CSV. Esta diferencia es pequeña en términos relativos (0.1%) pero indica que los archivos no se generaron en la misma ejecución del script. No hay evidencia de corrupción en el CSV (las celdas son normales).

**Posible causa:** El CSV puede corresponder a una versión anterior del SIGED con menos escuelas, y el GeoJSON a una versión más reciente. Se recomienda volver a correr el script para sincronizarlos.

---

### ✅ PAN — Panamá

**Fuente:** Marco Muestral MEDUCA + Georreferencia de Centros Educativos 2024  
**Año de datos:** 2024  
**Sector:** Oficial (excluye IPHE — institutos de educación especial)

- CSV: **3,132 filas** | GeoJSON: **3,132 features** ✅ sincronizados
- Georeferenciadas: **3,107 (99.2%)**

**[PAN-INFO-1]** 25 escuelas sin coordenadas. No hay campo de dirección disponible en el CSV procesado para estas escuelas (el script de PAN no incluye columna de dirección en el output).

---

### ✅ PER — Perú

**Fuente:** Padrón de Instituciones Educativas + Matrícula + Recursos  
**Año de datos:** 2024  
**Sector:** Pública directa + Pública gestión privada (excluye Privada)

- CSV: **69,142 filas** | GeoJSON: **69,142 features** ✅ sincronizados
- Georeferenciadas: **69,142 (100%)**
- Sin errores críticos detectados.

---

### ✅ PRY — Paraguay

**Fuente:** Establecimientos 2023 + Matriculaciones por nivel  
**Año de datos:** 2023  
**Sector:** Público (excluye "Privado" en el campo `sector_o_tipo_gestion`)

- CSV: **8,162 filas** | GeoJSON: **8,162 features** ✅ sincronizados
- Georeferenciadas: **7,900 (96.8%)**

**[PRY-INFO-1]** 262 escuelas sin coordenadas. El campo `direccion` está disponible en los datos crudos (`establecimientos_2023.csv`).

---

### 🟡 SLV — El Salvador

**Fuente:** `CE_2024 El Salvador.xlsx`  
**Año de datos:** 2024  
**Sector:** ADVERTENCIA — puede incluir privadas

- CSV: **5,160 filas** | GeoJSON: **5,160 features** ✅ sincronizados
- Georeferenciadas: **5,093 (98.7%)**

**[SLV-ERR-1] 🟡 MEDIO: Filtro de sector privado comentado**  
En la versión actual del script `SLV_script.qmd`, hay dos versiones del pipeline. La versión anterior (`base_inicial`) aplicaba el filtro `filter(sector== "Público")` que excluía 883 escuelas privadas. La versión activa (`base_nueva`, basada en `CE_2024 El Salvador.xlsx`) **no tiene filtro de sector aplicado**, ya que el código de filtro está comentado.

El archivo de coordenadas `SLV_coord_EDU.csv` (5,143 públicas + 883 privadas = 6,026 total) confirma que existen escuelas privadas. Si el `CE_2024` incluye privadas, el archivo procesado puede contener hasta 883 establecimientos privados no identificados.

**Acción requerida:** Verificar si `CE_2024 El Salvador.xlsx` incluye escuelas privadas. Si sí, aplicar el filtro de sector.

---

### ✅ SUR — Suriname

**Fuente:** `Suriname School List_03202024.xlsx`  
**Año de datos:** 2024  
**Sector:** Público + ~5 escuelas privadas ("Particulier")

- CSV: **547 filas** | GeoJSON: **547 features** ✅ sincronizados
- Georeferenciadas: **547 (100%)**

**[SUR-INFO-1]** El dataset incluye aproximadamente 5 escuelas privadas (`school_type == "Particulier"`), pero el CSV procesado no tiene columna de tipo de escuela que permita identificarlas. Son una fracción muy pequeña del total (< 1%).

---

### ✅ URY — Uruguay

**Fuente:** CEIP (shp) + CES (shp) + CETP (shp) — ANEP  
**Año de datos:** 2024  
**Sector:** Público (todo el sistema ANEP)

- CSV: **2,597 filas** | GeoJSON: **2,597 features** ✅ sincronizados
- Georeferenciadas: **2,597 (100%)**
- Sin errores críticos detectados.

---

## Tabla resumen de errores por país

| ISO | País | Errores críticos | Errores medios | Estado CSV | Estado GeoJSON |
|-----|------|-----------------|----------------|------------|----------------|
| ARG | Argentina | 1 (CSV corrupto) | 1 (desync) | 🔴 Corrupto | ✅ OK |
| BLZ | Belize | 0 | 0 | ✅ OK | ✅ OK |
| BOL | Bolivia | 0 | 0 | ✅ OK | ✅ OK |
| BRA | Brasil | 0 | 0 | ✅ OK | ✅ OK |
| BRB | Barbados | 0 | 2 (sin coords, sin dirección) | ✅ OK | ✅ OK |
| CHL | Chile | 0 | 0 | ✅ OK | ✅ OK |
| COL | Colombia | 0 | 0 | ✅ OK | ✅ OK |
| CRI | Costa Rica | 0 | 0 | ✅ OK | ✅ OK |
| DOM | R. Dominicana | 0 | 1 (datos 2022) | ✅ OK | ✅ OK |
| ECU | Ecuador | 1 (CSV corrupto) | 1 (desync grave) | 🔴 Corrupto | ✅ OK |
| GTM | Guatemala | 0 | 0 | ✅ OK | ✅ OK |
| GUY | Guyana | 0 | 1 (sin nivel cols) | 🟡 Incompleto | ✅ OK |
| HND | Honduras | 0 | 0 | ✅ OK | ✅ OK |
| JAM | Jamaica | 0 | 1 (script vacío) | 🟡 Sin auditar | 🟡 Sin auditar |
| MEX | México | 0 | 1 (desync menor) | ✅ OK | 🟡 Leve desync |
| PAN | Panamá | 0 | 0 | ✅ OK | ✅ OK |
| PER | Perú | 0 | 0 | ✅ OK | ✅ OK |
| PRY | Paraguay | 0 | 0 | ✅ OK | ✅ OK |
| SLV | El Salvador | 0 | 1 (puede incluir privadas) | 🟡 Incierto | ✅ OK |
| SUR | Suriname | 0 | 0 | ✅ OK | ✅ OK |
| URY | Uruguay | 0 | 0 | ✅ OK | ✅ OK |

---

## Tabla resumen de instituciones CIMA (K-12, por sector)

> **Nota:** El archivo `{ISO}_total_cima.csv` se construyó filtrando instituciones con al menos un nivel de primaria o secundaria (`nivel_primaria == 1 OR nivel_secbaja == 1 OR nivel_secalta == 1`). Para ARG y ECU se usó el GeoJSON como fuente (CSV corrupto).
> 
> **`Public*`** = mayoritariamente público pero puede incluir algunas privadas (SLV, SUR) o sector no identificado (BRB).

| ISO | País | Año datos | Total K-12 | Sector | Georef K-12 | Dirección disponible | Desglose subnacional |
|-----|------|-----------|-----------|--------|-------------|---------------------|---------------------|
| ARG | Argentina | 2023 | 27,898 | Public | 27,202 (97.5%) | Sí | ADM2 (partido) |
| BLZ | Belize | 2024 | 273 | Public | 273 (100%) | Sí | ADM1 (district) |
| BOL | Bolivia | 2023 | 14,918 | Public | 14,890 (99.8%) | Sí | ADM1 (departamento) |
| BRA | Brasil | 2023 | 55,321 | Public | 48,710 (88.1%) | Sí | ADM2 (municipio) |
| BRB | Barbados | 2024 | 94 | Public* | 0 (0%) ⚠ | No | Solo país |
| CHL | Chile | 2023 | 7,858 | Public | 7,858 (100%) | No | ADM2 (provincia) |
| COL | Colombia | 2023 | 43,281 | Public | 42,966 (99.3%) | Sí | ADM2 (municipio) |
| CRI | Costa Rica | 2024 | 4,327 | Public | 4,293 (99.2%) | Sí | ADM1 (provincia) |
| DOM | R. Dominicana | 2022 | 6,393 | Public | 6,093 (95.3%) | No | ADM2 (provincia) |
| ECU | Ecuador | 2024 | 12,518 | Public | 12,476 (99.7%) | No | ADM2 (cantón) |
| GTM | Guatemala | 2024 | 22,039 | Public | 22,039 (100%) | Sí | ADM1 (departamento) |
| GUY | Guyana | 2024 | — ⚠ | Public | — | Sí | ADM1 (region) |
| HND | Honduras | 2023 | 16,955 | Public | 16,234 (95.7%) | Sí | ADM1 (departamento) |
| JAM | Jamaica | 2024 | 914 | Unknown | 912 (99.8%) | No | Desconocido |
| MEX | México | 2024 | 132,339 | Public | 132,339 (100%) | Sí | ADM2 (municipio) |
| PAN | Panamá | 2024 | 3,090 | Public | 3,068 (99.3%) | No | ADM1 (provincia) |
| PER | Perú | 2024 | 43,412 | Public | 43,412 (100%) | Sí | ADM2 (provincia) |
| PRY | Paraguay | 2023 | 8,109 | Public | 7,853 (96.8%) | Sí | ADM2 (distrito) |
| SLV | El Salvador | 2024 | 4,888 | Public* | 4,826 (98.7%) | Sí | ADM1 (departamento) |
| SUR | Suriname | 2024 | 547 | Public* | 547 (100%) | Sí | ADM1 (district) |
| URY | Uruguay | 2024 | 2,395 | Public | 2,395 (100%) | Sí | ADM1 (departamento) |
| **TOTAL** | **20 países** | | **407,569** | | **398,386 (97.7%)** | | |

---

## Acciones prioritarias recomendadas

### Prioridad 1 — Acción inmediata
1. **Regenerar `ECU_total.csv`**: pierde el 50% de las escuelas (6,385 filas). Correr `ECU_script.qmd`.
2. **Regenerar `ARG_total.csv`**: pierde 2,221 filas. Correr `ARG_script.qmd`.

### Prioridad 2 — Acción a corto plazo
3. **Resolver GUY**: agregar columnas `nivel_` al output de `procesar_datos()`.
4. **Revisar SLV**: verificar si `CE_2024 El Salvador.xlsx` contiene privadas y aplicar filtro.
5. **Sincronizar MEX**: 227 features de diferencia entre CSV y GeoJSON. Volver a correr el script.

### Prioridad 3 — Acción a mediano plazo
6. **Documentar JAM**: construir script de procesamiento y obtener datos crudos del ministerio.
7. **Actualizar DOM**: usar datos 2023-2024 disponibles en la fuente.
8. **Agregar coordenadas a BRB**: el GeoJSON tiene geometrías, el CSV no. Revisar exportación.
9. **Geocodificar sin coordenadas**: BRA (17,876), HND (721), DOM (305), PRY (262), COL (399) — usar direcciones disponibles.

---

## Corrección crítica: archivos CIMA deben procesarse desde datos crudos (v2 — 2026-03-23)

### Error de diseño identificado en la versión v1

Los archivos `{ISO}_total_cima.csv` generados en la primera versión fueron construidos a partir de los CSV/GeoJSON ya procesados por los scripts R. **Estos archivos ya excluían las escuelas privadas**, porque la mayoría de los scripts R aplican filtros de sector (ej. `sector == 1`, `sector != "PRIVADO"`, `admin_category == "Pública"`) antes de exportar.

Esto significa que la columna `sector = "Public"` en la v1 era correcta para las escuelas incluidas, pero **el universo estaba incompleto**: no había escuelas privadas.

### Solución aplicada en v2

Se reconstruyeron todos los archivos CIMA directamente desde los **archivos crudos del ministerio**, eliminando los filtros de sector pero conservando todos los demás filtros (nivel K-12, activas, sistema regular). Se añadió la columna `sector = "Public" / "Private"` desde la fuente original.

### Diferencias de conteo v1 vs v2 (K-12 totales)

| ISO | v1 (solo públicas) | v2 (público + privado) | Privadas recuperadas | Fuente sector |
|-----|--------------------|------------------------|----------------------|---------------|
| ARG | ~27,953 | 35,368 | 7,415 | `sector` (1=Public, 2=Private) |
| BOL | 14,918 | 15,564 | 646 | `dependencia` (Privada) |
| BRA | 104,110 | 129,976 | 25,866 | `TP_DEPENDENCIA` (4=Privada) |
| CHL | 5,190 | 8,444 | 3,254 | `COD_DEPE` (3=Part.Pagado) |
| COL | 42,538 | 48,209 | 5,671 | `sector_id` (2=Privado) |
| CRI | 4,350 | 4,351 | 1 | `DEPENDENCIA` (PRI) |
| DOM | 6,480 | 8,980 | 2,500 | `sector` (PRIVADO) |
| ECU | 13,077 | 16,215 | 3,138 | `sostenimiento` (Particular) |
| MEX | 135,831 | 156,830 | 20,999 | `control` (PRIVADO) |
| PAN | 3,090 | 3,615 | 525 | `dependencia` (PARTICULAR) |
| PER | 40,153 | 53,342 | 13,189 | `GESTION` (3=Privada) |
| PRY | 7,047 | 7,628 | 581 | `sector_o_tipo_gestion` (Privado) |
| SLV | 4,880 | 5,763 | 883 | `SECTOR` (Privado) — SLV_coord_EDU.csv |
| SUR | 567 | 572 | 5 | `school_type` (Particulier) |

### Países donde solo existe registro público en la fuente cruda

| ISO | Motivo |
|-----|--------|
| BLZ | Solo escuelas governmentales en el archivo del ministerio |
| BRB | No hay columna de sector en el archivo fuente |
| GTM | SIRE registra principalmente escuelas MINEDUC; solo 4 privadas detectadas |
| GUY | Sistema National/Community = todo público |
| HND | SIPLIE es el sistema del gobierno; no registra privadas |
| HTI | Datos PAPDEF (MENFP); sin desglose de sector |
| JAM | Sin datos crudos disponibles |
| URY | ANEP (sistema público); sin datos privados en la fuente |

### Limitaciones de la v2

- **BRA**: Sin coordenadas — el archivo de microdatos no incluye latitud/longitud. Las coordenadas del pipeline original provienen de `geobr::read_schools()` (paquete R), que no es reproducible en Python sin acceso a internet. Solución: regenerar desde R o usar el GeoJSON original solo para escuelas públicas.
- **CRI**: Sin coordenadas — el archivo NominaCentros no incluye georreferenciación. Requiere fuente separada para geocodificar.
- **CRI sector**: Solo se detectó 1 escuela privada en el NominaCentros2024.xlsx. Es posible que las escuelas privadas reporten a otra fuente.
- **GTM sector privado**: Solo 4 escuelas privadas en el SIRE. El SIRE principalmente registra escuelas MINEDUC (públicas/cooperativas). Las privadas guatemaltecas pueden estar subregistradas.
- **SUR**: Sin coordenadas — el archivo de lista de escuelas de Surinam no incluye lat/lon.

### Script de reproducción

Ver `_build_cima_v2.py` en la raíz del proyecto. Resultados guardados en `results/cima_v2_summary.csv`.

---

## Auditoría de fuentes y reconciliación de conteos: ISO_total vs ISO_total_cima (2026-03-23)

### Objetivo

Verificar que todos los archivos utilizados por los scripts QMD estén correctamente incorporados en el pipeline CIMA v2, y explicar las diferencias de conteo entre `{ISO}_total.csv` (procesado original, todas las variables) y `{ISO}_total_cima.csv` (K-12, sector, coordenadas).

---

### Hallazgo 1 — Bahamas (BHS) no tenía archivo CIMA

**Error identificado:** El script `_build_cima_v2.py` no incluía función `process_BHS()`. Por tanto, no existía `BHS_total_cima.csv`.

**Causa raíz:** El QMD de BHS es rudimentario (solo lee el shapefile, sin procesamiento adicional) y fue omitido durante la construcción del pipeline CIMA.

**Corrección:** Se añadió `process_BHS()` que lee `bhs_schools_shp/bhs_schools.shp` (77 escuelas con coordenadas). Como el dataset es un POI sin información de nivel ni sector, se asume K-12 genérico y sector `Unknown`. Se generó `BHS_total_cima.csv`.

**Limitación residual:** BHS solo cuenta con un dataset de Puntos de Interés (POI) sin desglose de nivel educativo ni clasificación público/privado.

---

### Hallazgo 2 — Archivos en QMD no usados en CIMA: clasificación

Se auditaron todos los archivos referenciados en los scripts QMD y se clasificaron en cuatro categorías respecto al pipeline CIMA:

| Categoría | Descripción | Países | ¿Acción requerida? |
|---|---|---|---|
| **Métricas de calidad educativa** | Datos de IDEB, SIMCE, matrícula, dotación docente, TIC, recursos. Enriquecen el ISO_total pero no son fuente de registro de escuelas. | BRA, CHL, COL, PER, SLV | No — correctamente excluidos del CIMA |
| **Archivos de validación espacial** | Shapefiles de límites administrativos LAC usados para chequeo de coordenadas | Todos | No — irrelevantes para CIMA |
| **Código comentado en QMD** | SIPLIE_Georef.xlsx y Giga_Georef.xlsx de HND están explícitamente comentados; KMZ/CSV de URY son enfoques explorados y descartados | HND, URY | No — nunca utilizados en el pipeline |
| **Fuente de coordenadas alternativa no integrable** | HTI: shapefile OSM tiene coordenadas pero sin ID de escuela, nivel ni sector. No se puede integrar sin geocodificación por nombre. | HTI | Documentar como limitación |

**Archivos correctamente utilizados por CIMA (incluyendo los de fuentes secundarias identificados en sesión anterior):**
- COL: `Colombia_CE_coordenadas.csv` (coordenadas) ✓
- CRI: `20250711_MEP_CE_PUBLICOS.xlsx` (coordenadas escuelas públicas) ✓
- ECU: `mineduc_ies_20242025_02122024/ie_2024_2025.shp` (coordenadas) ✓
- PAN: `Anexo 2 - Georreferencia de Centros Educativos.xlsx` (coordenadas) ✓
- SLV: `SLV_coord_EDU.csv` (coordenadas + privadas) ✓
- URY: `CEIP.shp`, `CES.shp`, `CETP.shp` (primaria, secundaria, técnica) ✓
- BHS: `bhs_schools_shp/bhs_schools.shp` (ahora integrado) ✓ *(corrección de esta sesión)*

---

### Hallazgo 3 — Reconciliación de conteos ISO_total vs ISO_total_cima

La tabla siguiente documenta todas las diferencias entre el dataset procesado original (`ISO_total`) y el nuevo CIMA v2 (`ISO_total_cima`), con justificación de cada brecha.

| ISO | ISO_total | Georef_total | CIMA_total | Pub | Prv | Georef_CIMA | Diferencia | Justificación |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| ARG | 35,636 | 34,166 | 35,368 | 27,953 | 7,415 | 34,394 | −268 | CIMA excluye escuelas de nivel inicial (educación temprana) que sí incluye el ISO_total |
| BHS | — | — | 77 | — | — | 77 | N/A | ISO_total inexistente; CIMA construido de POI (sin nivel/sector) |
| BLZ | 303 | 303 | 273 | 273 | 0 | 273 | −30 | CIMA filtra K-12; algunas escuelas del ISO_total son de nivel preescolar |
| BOL | 15,329 | 15,299 | 15,564 | 14,918 | 646 | 15,533 | +235 | CIMA incluye privadas no capturadas en ISO_total (que era público-priorizado) |
| BRA | 134,418 | 116,542 | 129,976 | 104,110 | 25,866 | 0 | −4,442 | CIMA filtra K-12; ISO_total incluye educación inicial, EJA (adultos) y educación especial. BRA sin coordenadas en ambos (origen: paquete R `geobr`) |
| BRB | 106 | 106 | 94 | 94 | 0 | 94 | −12 | Algunas escuelas del ISO_total no ofrecen educación K-12 |
| CHL | 7,895 | 7,895 | 8,444 | 5,190 | 3,254 | 8,438 | +549 | **Error en ISO_total:** R script filtraba `sostenimiento != "Particular"` (solo públicas). CIMA corrige incluyendo privadas |
| COL | 43,658 | 43,259 | 48,209 | 42,538 | 5,671 | 47,587 | +4,551 | CIMA incluye sedes privadas DANE no incorporadas en ISO_total |
| CRI | 4,418 | 4,381 | 4,351 | 4,350 | 1 | 4,279 | −67 | CIMA es K-12 estricto; ISO_total incluye centros con nivel inicial únicamente. Solo 1 privada detectada (limitación: privadas CRI pueden reportar a otra fuente) |
| DOM | 6,599 | 6,294 | 8,980 | 6,480 | 2,500 | 6,244 | +2,381 | **Error en ISO_total:** pipeline original tenía filtro de año que excluía privadas. CIMA corrige incluyendo 2,500 privadas |
| ECU | 6,382 | 6,357 | 16,215 | 13,077 | 3,138 | 15,688 | +9,833 | **Error más significativo:** R script filtraba `sostenimiento != "Particular"` explícitamente. ISO_total solo tenía escuelas públicas (6k). CIMA incluye ~3,100 privadas y corrige el total real (16k) |
| GTM | 35,973 | 35,973 | 35,350 | 35,346 | 4 | 35,350 | −623 | CIMA excluye escuelas sin oferta K-12 (preprimaria) del SIRE. Solo 4 privadas detectadas — subregistro probable en SIRE |
| GUY | 874 | 874 | 546 | 546 | 0 | 545 | −328 | ISO_total incluye 328 escuelas de guardería/nursery (tipo N). CIMA filtra correctamente K-12 únicamente |
| HND | 16,955 | 16,234 | 16,926 | 16,926 | 0 | 16,336 | −29 | CIMA excluye nivel Pre-Básica. SIPLIE_Georef.xlsx y Giga_Georef.xlsx estaban comentados en QMD y no aportan datos adicionales |
| HTI | — | — | 111 | 111 | 0 | 0 | N/A | ISO_total inexistente. CIMA usa PAPDEF (111 escuelas, sin coordenadas). OSM shapefile tiene coordenadas pero no tiene nivel/sector/ID — no integrable sin geocodificación por nombre |
| JAM | 955 | 953 | 914 | 0 | 0 | 912 | −41 | QMD vacío, sin datos crudos del ministerio. CIMA construido desde ISO_total (K-12 filtrado). Sector desconocido para todas las escuelas |
| MEX | 205,848 | 205,848 | 156,830 | 135,831 | 20,999 | 156,830 | −49,018 | **Diferencia esperada:** ISO_total es público + preescolar (49k escuelas de nivel inicial). CIMA es K-12 público+privado. Nota: ISO_total original era público únicamente |
| PAN | 3,132 | 3,107 | 3,615 | 3,090 | 525 | 3,068 | +483 | CIMA incluye 525 privadas no en ISO_total |
| PER | 69,142 | 69,142 | 53,342 | 40,153 | 13,189 | 53,342 | −15,800 | ISO_total es público con inicial+K-12. CIMA es K-12 público+privado. Diferencia = inicial público (~29k) menos privadas K-12 añadidas (13k). **ISO_total original era solo gestión pública** |
| PRY | 8,162 | 7,900 | 7,628 | 7,047 | 581 | 7,275 | −534 | CIMA excluye educación inicial. ISO_total incluía educación inicial |
| SLV | 5,160 | 5,093 | 5,763 | 4,880 | 883 | 5,637 | +603 | CIMA incluye 883 privadas (identificadas en SLV_coord_EDU.csv) que el ISO_total no tenía |
| SUR | 547 | 547 | 572 | 567 | 5 | 572 | +25 | CIMA añade 5 privadas. Diferencia en total por ajuste de criterios K-12 |
| URY | 2,597 | 2,597 | 2,611 | 2,611 | 0 | 2,611 | +14 | CIMA lee directamente de shapefiles CEIP+CES+CETP. Diferencia de 14 escuelas por distinto tratamiento de duplicados en `procesar_datos()` |

---

### Resumen ejecutivo de errores de omisión en ISO_total

Los siguientes países tenían **escuelas privadas sistemáticamente excluidas** del ISO_total por filtros explícitos en el R script original. Los conteos CIMA v2 son los correctos:

| País | Filtro en R original | Privadas omitidas | Fuente |
|---|---|---|---|
| ECU | `sostenimiento != "Particular"` | ~3,138 | QMD línea 25 y 51 |
| CHL | `sostenimiento != "Particular"` | ~3,254 | QMD (shapefile + CSV) |
| PER | `d_gestion != "Privada"` | ~13,189 | QMD línea 32 |
| DOM | Filtro de año eliminaba privadas | ~2,500 | QMD (filtro implícito) |
| MEX | `control == "PÚBLICO"` | ~20,999 | QMD línea 152 |

**Nota:** BOL, COL, PAN y SLV también presentan diferencias positivas en CIMA que sugieren subregistro de privadas en el ISO_total, aunque el filtro no era tan explícito en el R script.

---

### Script de auditoría

Ver `_audit_pipeline.py` en la raíz del proyecto. Resultados guardados en `results/count_reconciliation.csv`.

---

*Generado automáticamente por `_build_cima.py` (v1) y `_build_cima_v2.py` (v2) | Revisión manual de scripts QMD por analista*
