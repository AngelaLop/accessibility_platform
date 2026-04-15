# School Accessibility Platform

### Inter-American Development Bank (IDB/BID)

Municipality-level indicators of school accessibility and equity for **21 Latin American and Caribbean countries**. Covers ~530,000 K-12 schools (public + private) to support education infrastructure budgeting, planning, and accountability across the region.

---

## 1. Pipeline Overview

The platform is built in two phases: **data preparation** (cleaning, geocoding, quality control) and **indicator computation** (travel time modeling, population analysis, final metrics).

```
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                                                                             │
 │    PHASE A: DATA PREPARATION                                                │
 │                                                                             │
 │    Raw Ministry ──> 01 Build CIMA ──> 02 QC Coordinates ──> 03 Coverage     │
 │    Files (23)       (standardize)     (spatial validation)   (vs universe)   │
 │                          │                    │                              │
 │                          ▼                    ▼                              │
 │                     05 Geocode ────────> CIMA Files                          │
 │                     (fill gaps +          per country                        │
 │                      score-based QC)     (.csv, 18 cols)                     │
 │                                                                             │
 └──────────────────────────────────────────┬──────────────────────────────────┘
                                            │
 ┌──────────────────────────────────────────▼──────────────────────────────────┐
 │                                                                             │
 │    PHASE B: INDICATOR COMPUTATION                                           │
 │                                                                             │
 │    06 School Base ──────────────┐                                           │
 │    (merge + spatial join ADM2)  │                                           │
 │                                 ▼                                           │
 │    07 Population ──────> 10 Compute ──────> INDICATOR TABLES                │
 │    (WorldPop zonal)      Indicators         (ADM2 x level)                  │
 │                              ▲                                              │
 │    07 Socioeconomic ─────────┤             Output formats:                  │
 │    (IDB poverty + Meta RWI)  │             - Parquet (analytics)            │
 │                              │             - Excel (BID deliverable)        │
 │    08 Friction ───> 09 FMM ──┘             - GeoPackage (GIS)              │
 │    (MAP + OSM)      (travel time)                                           │
 │                                                                             │
 └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Model

Six interconnected tables feed the final indicator computation. The central entity is the **ADM2 municipality** (12,531 polygons across LAC).

```
                              ┌─────────────────────┐
                              │    admin_units       │
                              │    (12,531 ADM2)     │
                              │                     │
                              │  PK: adm2_pcode     │
                              │  adm0/1_pcode       │
                              │  adm0/1/2_en        │
                              │  geometry            │
                              │  area_km2            │
                              └──────────┬──────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
              ▼                          ▼                          ▼
 ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
 │   school_base      │   │  adm2_population   │   │ adm2_socioeconomic │
 │   (~530,000 rows)  │   │  (12,531 rows)     │   │ (12,531 rows)      │
 │                    │   │                    │   │                    │
 │  PK: adm0 + id_nac│   │  PK: adm2_pcode    │   │  PK: adm2 + source │
 │  id_edificio       │   │  pop_primary_6to11 │   │  poverty_rate (IDB)│
 │  sector            │   │  pop_second_12to14 │   │  nbi_rate (IDB)    │
 │  nivel_pri/sec/alt │   │  pop_highsch_15to17│   │  rwi_mean (Meta)   │
 │  latitud, longitud │   │  pop_total_6to17   │   │  rwi_std (Meta)    │
 │  coordinate_quality│   │                    │   │  data_year         │
 │  adm1/2_pcode      │   │  Source: WorldPop  │   │                    │
 │  data_year         │   │  1km rasters       │   │  Sources:          │
 │                    │   │                    │   │  IDB Poverty Maps  │
 │  Source: CIMA files│   └────────┬───────────┘   │  Meta RWI raster   │
 │  + spatial join    │            │               └────────┬───────────┘
 └────────┬───────────┘            │                        │
          │                        │                        │
          │         ┌──────────────┴────────────────────────┘
          │         │
          ▼         ▼
 ┌──────────────────────────────────────────────┐
 │              indicators_adm2                  │
 │          (~37,500 rows: 12,531 x 3 levels)   │
 │                                              │
 │  PK: adm2_pcode + education_level            │
 │                                              │
 │  Supply:     n_schools, n_public, n_private  │
 │  Demand:     pop_school_age                  │
 │  Ratio:      school_per_1000_pop             │
 │  Access:     pct_within_15/30/60min_motor    │
 │              pct_within_15/30/60min_walk      │
 │              mean_travel_min_motor/walk       │
 │  Equity:     poverty_rate, rwi_mean          │
 │  Quality:    data_completeness               │
 │  Class:      exclusion_severity              │
 │              (optimal/adequate/signif/severe) │
 │                                              │
 │  Aggregated to: ADM2, ADM1, ADM0             │
 └───────────────▲──────────────────────────────┘
                 │
 ┌───────────────┴──────────────────┐
 │       travel_time_zonal          │
 │    (~12,531 rows / scenario)     │
 │                                  │
 │  PK: scenario_id + adm2_pcode   │
 │  pop_within_15/30/60min          │
 │  pct_within_30min                │
 │  mean_travel_min                 │
 │                                  │
 │  Source: FMM (scikit-fmm)        │
 │  on MAP/OSM friction surfaces    │
 └──────────────────────────────────┘

 ┌──────────────────────────────────┐
 │         school_qc                │  (separate audit table,
 │      (~530,000 rows)             │   not used for indicators)
 │                                  │
 │  Full geocoding history:         │
 │  original + geocoded coords      │
 │  arcgis_score, acceptance        │
 │  admin boundary match results    │
 │  nombre_centro (for reference)   │
 └──────────────────────────────────┘
```

---

## 3. Geocoding Quality Framework

### The Problem

~6% of schools (~30,000) lack GPS coordinates from ministry data. Geocoding can fill these gaps, but **how reliable is the geocoder?**

### Ground Truth Validation

We tested geocoder accuracy by geocoding **550 schools with known GPS** across 11 countries — then measuring how far the geocoded result fell from the real location.

```
   Ground Truth Results: Geocoder Error by ArcGIS Score
   ────────────────────────────────────────────────────
   Score >= 95 ██░░░░░░░░░░░░░░░░░░░░  0.2 km median  (87% < 5km)
   Score 90-95 ████████░░░░░░░░░░░░░░  4.4 km median  (51% < 5km)
   Score < 90  ████████████████░░░░░░  8.1 km median  (40% < 5km)
   ────────────────────────────────────────────────────
               0    2    4    6    8   10 km
```

### Score-Based Rules

| ArcGIS Score | Classification | Median Error | Action (FILL) | Action (COMPARE) |
|---|---|---|---|---|
| >= 95 | `street` | 0.2 km | Accept | Keep GPS, log alternative |
| 90 - 95 | `centroid` | 4.4 km | Accept as centroid | Keep GPS, flag discrepancy |
| < 90 | `uncertain` | 8.1 km | **Reject** (leave empty) | Keep GPS, flag discrepancy |

**Key principle:** GPS from the ministry is always preserved. The geocoder only **fills gaps** where no coordinate exists. It never replaces existing GPS.

### Geocoder Accuracy by Country

```
   Ground Truth: Median Geocoder Error (km)
   ──────────────────────────────────────────────
   SUR ██                                0.2 km   Score: 97.9
   BRA ███                               1.3 km   Score: 95.5
   MEX ███                               1.5 km   Score: 91.5
   GTM ████                              1.6 km   Score: 87.7
   ARG ████                              2.1 km   Score: 92.1
   CRI ████████                          4.0 km   Score: 86.0
   COL ████████                          4.3 km   Score: 90.7
   PER ██████████                        5.3 km   Score: 94.1
   PRY ████████████                      5.8 km   Score: 83.2
   BOL █████████████                     6.8 km   Score: 80.6
   HND █████████████████                 8.6 km   Score: 80.0
   ──────────────────────────────────────────────
        0    2    4    6    8   10 km
```

Evidence: `results/geocoder_ground_truth_all_countries.csv` (550 schools)

---

## 4. Coordinate Quality Classification

Every school in the final database carries a `coordinate_quality` label:

| Quality | Meaning | Count | Use in Analysis |
|---|---|---|---|
| `gps` | Ministry GPS, confirmed in declared municipality | ~500,000 | Full confidence |
| `street` | Geocoded, ArcGIS score >= 95 | ~1,000 | High confidence |
| `centroid` | Geocoded, ArcGIS score 90-95 (municipal centroid) | ~2,000 | Use with caution |
| `flag` | Has GPS but address doesn't match location | ~2,000 | GPS preserved, discrepancy noted |
| _(empty)_ | No coordinate available | ~25,000 | Excluded from spatial analysis |

---

## 5. Urban/Rural Classification

Each 1km WorldPop pixel is classified into one of three settlement categories based on population density and total population:

```
   Classification             Density         Population
   ──────────────────────────────────────────────────────
   Urban                      >= 300 hab/km2  >= 5,000
   Semi-urban (No urbano)     >= 150 hab/km2  200 - 5,000
   Dispersed                  < 150 hab/km2   < 200
   ──────────────────────────────────────────────────────
```

This classification is applied in step 07 (zonal population) and propagated to step 10 (indicators), enabling disaggregation of all accessibility metrics by settlement type. Schools in `school_base` also carry an `area_class` label (urban / semi-urban / dispersed) based on the WorldPop pixel at their location.

Thresholds are defined in `definitions.md`. How to treat each category in the final indicators (include, exclude, or report separately) is a policy decision to be defined with the BID team.

---

## 6. Indicator Definitions

### Supply Indicators
- **n_schools**: Number of K-12 schools offering each education level in the municipality
- **school_per_1000_pop**: Schools per 1,000 school-age population

### Accessibility Indicators (from FMM travel time model)
- **pct_within_15min_motor/walk**: % of school-age population within 15 minutes of nearest school
- **pct_within_30min_motor/walk**: % within 30 minutes (primary threshold)
- **pct_within_60min_motor/walk**: % within 60 minutes
- **mean_travel_min**: Population-weighted average travel time to nearest school

### Equity Indicators
- **poverty_rate**: Subnational poverty headcount (IDB poverty maps, 2010-2020)
- **rwi_mean**: Meta Relative Wealth Index (2.4km resolution, satellite-derived)
- **exclusion_severity**: Classification based on % within 30 min motorized:
  - `optimal` (> 95%), `adequate` (80-95%), `significant` (50-80%), `severe` (< 50%)

### Education Levels
| Level | Variable | Ages | Description |
|---|---|---|---|
| Primary | `nivel_primaria` | 6-11 | Grades 1-6 (Primaria/Fundamental) |
| Lower Secondary | `nivel_secbaja` | 12-14 | Grades 7-9 (Secundaria Baja/Basica) |
| Upper Secondary | `nivel_secalta` | 15-17 | Grades 10-12 (Media/Bachillerato) |

---

## 7. Travel Time Methodology

Proven in the **Panama Pilot** (3,617 schools, documented in `docs/Final_Project_Lopez_Sanchez_Draft.pdf`).

```
   Schools          Friction Surface        Travel Time Surface
   (wavefront       (MAP or OSM,            (minutes to nearest
    sources)         1km resolution)          school)

   * * *            ░░▓▓▓▓░░░░░░           0  5  15  30  60  >60
     * *      x     ░▓▓████▓▓░░░     =     ■■ ■■ ▒▒ ░░ ░░  ··
   * * * *          ░░▓▓▓▓░░░░░░           ■■ ▒▒ ▒▒ ░░ ··  ··
                    ░░░░░░░░░░░░           ▒▒ ░░ ░░ ·· ··  ··

   Fast Marching Method (scikit-fmm):
   Propagates minimum travel time from all school sources
   simultaneously through the friction surface.
```

**Two friction sources compared:**
- **MAP** (Malaria Atlas Project, Weiss et al. 2020): Global, validated, motorized + walking
- **OSM** (OpenStreetMap): Custom rasterization of road network, captures recent infrastructure

**Panama results:** 96.7% within 15 min (motorized), 84.1% (walking). Education gradient: primary ~universal, upper secondary drops to 67.6% walking within 30 min.

---

## 8. Data Sources

| Source | Coverage | Resolution | Use |
|---|---|---|---|
| Ministry school registries | 21 countries | School-level | School locations, levels, sector |
| OCHA/UNICEF boundaries | LAC region | ADM0/1/2 polygons | Geographic units (12,531 ADM2) |
| WorldPop 2023 | Global | 1 km raster | School-age population by age group |
| MAP friction (2020) | Global | 1 km raster | Motorized + walking travel cost |
| OpenStreetMap | Global | Vector (roads) | Custom friction surfaces |
| IDB Poverty Maps | 21 countries | ADM1/ADM2 | Poverty headcount, NBI |
| Meta Relative Wealth Index | Global | 2.4 km raster | Satellite-derived wealth proxy |
| Panama Census 2023 | Panama | Point-level | Validation of WorldPop estimates |

---

## 9. Implementation Roadmap

| Phase | Step | Description | Environment | Status |
|---|---|---|---|---|
| **A** | 01 | Build CIMA files from raw ministry data | Local | Done (23 countries) |
| **A** | 02 | Coordinate QC vs admin boundaries | Local | Done (14 countries) |
| **A** | 03 | Coverage assessment vs official universe | Local | Done |
| **A** | 05 | Geocode missing + score-based QC | Local | HND done, COL in progress |
| **B** | 06 | Build school_base (merge + spatial join) | Local | Pending |
| **B** | 07 | Population + socioeconomic zonal stats | Local | Pending |
| **B** | 08 | Build friction surfaces (MAP + OSM) | Colab | Pending |
| **B** | 09 | FMM travel time computation | Colab | PAN pilot done |
| **B** | 10 | Compute final indicators | Local | Pending |

---

## 10. Running the Pipeline

```bash
# All scripts run from project root with uv (https://docs.astral.sh/uv/)
uv run python pipeline/01_build_cima.py              # Build CIMA files
uv run python pipeline/02_qc_coordinates.py          # Coordinate QC
uv run python pipeline/03_coverage_assessment.py      # Coverage report
uv run python pipeline/05_geocode_missing.py --countries HND   # Geocode one country
uv run python pipeline/05_geocode_missing.py --dry-run         # Preview targets

# Tests
uv run pytest tests/ -v
```

---

## 11. Repository Structure

```
accessibility_platform/
├── pipeline/                        # Numbered pipeline scripts
│   ├── 01_build_cima.py             # Build CIMA from raw ministry data (23 countries)
│   ├── 02_qc_coordinates.py         # Coordinate validation + admin boundary match
│   ├── 03_coverage_assessment.py    # Coverage vs official universe
│   ├── 04_qc_figures.py             # QC visualizations
│   ├── 05_geocode_missing.py        # Geocoding with score-based QC
│   └── run_all.py                   # Run full pipeline in sequence
├── tests/                           # pytest test suite
│   ├── test_cima_schema.py          # Schema validation
│   ├── test_coordinates.py          # Coordinate quality
│   ├── test_counts.py               # Count validation
│   └── test_geocoding.py            # Geocoding acceptance rules
├── data/
│   ├── schools/AR/{ISO}/raw/        # Raw ministry files (23 countries)
│   ├── schools/AR/{ISO}/processed/  # Standardized CIMA outputs
│   ├── bounderys/LAC/               # ADM0/1/2 boundaries (OCHA/UNICEF)
│   └── population/WorldPop/LAC/     # School-age population rasters (1km)
├── results/                         # Pipeline outputs
│   ├── qc_coordinate_report.csv     # Per-school coordinate validation
│   ├── geocode_results.csv          # Geocoding decisions + scores
│   ├── geocoder_ground_truth_*.csv  # Ground truth validation (550 schools)
│   └── presentacion_BID/            # BID presentation materials
├── Official Subnational Poverty Rates/  # IDB poverty data (ADM1/ADM2)
├── docs/                            # Academic deliverables
│   └── Final_Project_Lopez_Sanchez_Draft.pdf  # Panama pilot paper
├── CLAUDE.md                        # Full technical documentation
├── definitions.md                   # Indicator definitions
└── pyproject.toml                   # Python project config (uv)
```

