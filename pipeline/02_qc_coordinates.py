"""
QC and gap-filling for school coordinate data across 15 LAC countries.

Task A: Validate reported coordinates against stated admin units (spatial join).
Task B: Geocode schools missing coordinates using address data (Nominatim).

Usage:
    python _qc_coordinates.py              # Run both QC + geocoding
    python _qc_coordinates.py --qc-only    # Run QC validation only (no geopy needed)
"""

import sys
import json
import argparse
import unicodedata
from pathlib import Path

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path("data/schools/AR")
BOUNDS_DIR = Path("data/bounderys/LAC")
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)
GEOCODE_CACHE_PATH = RESULTS / "geocode_cache.json"

# ---------------------------------------------------------------------------
# Known ADM1 name aliases (raw data name → boundary name, after normalization)
# These are not errors — just naming differences between data sources.
# ---------------------------------------------------------------------------
ADM1_ALIASES = {
    "MEX": {"ciudad de mexico": "distrito federal"},
    "GTM": {"ciudad capital": "guatemala"},
    "PRY": {"capital": "asuncion"},
    "GUY": {
        "region 1": "barima-waini",
        "region 2": "pomeroon-supenaam",
        "region 3": "essequibo islands-west demerara",
        "region 4": "demerara-mahaica",
        "region 5": "mahaica berbice",
        "region 6": "east berbice-corentyne",
        "region 7": "cuyuni-mazaruni",
        "region 8": "potaro-siparuni",
        "region 9": "upper takutu-upper essequibo",
        "region 10": "upper demerara-berbice",
        "region 11": "demerara-mahaica",  # Region 11 not in boundaries; closest is Demerara-Mahaica
    },
}

# ---------------------------------------------------------------------------
# Country bounding boxes (generous, for pre-check)
# ---------------------------------------------------------------------------
COUNTRY_BOUNDS = {
    "ARG": {"lat": (-56, -21), "lon": (-74, -53)},
    "BLZ": {"lat": (15.5, 18.6), "lon": (-89.5, -87.3)},
    "BOL": {"lat": (-23, -9), "lon": (-70, -57)},
    "BRA": {"lat": (-34, 6), "lon": (-74, -34)},
    "COL": {"lat": (-5, 14), "lon": (-82, -66)},
    "CRI": {"lat": (8, 11.3), "lon": (-86, -82.5)},
    "GTM": {"lat": (13.5, 18), "lon": (-92.5, -88)},
    "GUY": {"lat": (1, 9), "lon": (-62, -56)},
    "HND": {"lat": (12.5, 16.5), "lon": (-90, -83)},
    "MEX": {"lat": (14, 33), "lon": (-118, -86)},
    "PER": {"lat": (-18.5, 0.5), "lon": (-82, -68)},
    "PRY": {"lat": (-28, -19), "lon": (-63, -54)},
    "SLV": {"lat": (13, 14.5), "lon": (-90.2, -87.6)},
    "SUR": {"lat": (1.8, 6.1), "lon": (-58.1, -53.9)},
    "URY": {"lat": (-35.2, -30), "lon": (-58.5, -53)},
}

# ---------------------------------------------------------------------------
# Country address config — one entry per country with address data
# ---------------------------------------------------------------------------
COUNTRY_CONFIG = {
    "ARG": {
        "raw_file": "raw/6831 - Listado de establecimientos con caracteristicas básicas.csv",
        "read_fn": "csv",
        "read_kwargs": {"sep": ";", "encoding": "latin-1", "low_memory": False},
        "id_col": "cueanexo",
        "adm1_col": "provincia",
        "adm2_col": "departamento",
        "locality_col": "localidad",
        "street_col": "ndomicilio",
        "country_name": "Argentina",
    },
    "BLZ": {
        "raw_file": "raw/geo_schools Belize.xlsx",
        "read_fn": "excel",
        "read_kwargs": {},
        "id_col": "Code",
        "adm1_col": "Area Administrative",
        "adm2_col": None,
        "locality_col": None,
        "street_col": "Address",
        "country_name": "Belize",
    },
    "BOL": {
        "raw_file": "raw/MinEdu_InstitucionesEducativas_2023.xlsx",
        "read_fn": "excel",
        "read_kwargs": {"skiprows": 7},
        "id_col": "Codigo R.U.E.",
        "adm1_col": "Departamento",
        "adm2_col": "Municipio",
        "locality_col": None,
        "street_col": "Dirección",
        "country_name": "Bolivia",
    },
    "BRA": {
        "raw_file": "raw/microdados_censo_escolar_2023/dados/microdados_ed_basica_2023.csv",
        "read_fn": "csv",
        "read_kwargs": {"sep": ";", "encoding": "latin-1", "low_memory": False},
        "usecols": [
            "CO_ENTIDADE", "NO_UF", "SG_UF", "NO_MUNICIPIO",
            "CO_MUNICIPIO", "DS_ENDERECO", "NU_ENDERECO", "NO_BAIRRO",
        ],
        "id_col": "CO_ENTIDADE",
        "adm1_col": "NO_UF",
        "adm2_col": "NO_MUNICIPIO",
        "locality_col": "NO_BAIRRO",
        "street_col": "DS_ENDERECO",
        "country_name": "Brazil",
    },
    "COL": {
        "raw_file": "raw/DANE_2023/Carátula única de la sede educativa.CSV",
        "read_fn": "csv",
        "read_kwargs": {"encoding": "latin-1", "engine": "python", "on_bad_lines": "skip"},
        "id_col": "SEDE_CODIGO",
        "adm1_col": "DEPTO",
        "adm2_col": "MUNI",
        "locality_col": "LOCALIDAD",
        "street_col": "SEDE_DIRECCION",
        "country_name": "Colombia",
    },
    "CRI": {
        "raw_file": "raw/20250711_MEP_CE_PUBLICOS.xlsx",
        "read_fn": "excel",
        "read_kwargs": {},
        "id_col": "CODPRES",
        "adm1_col": "PROVINCIA",
        "adm2_col": "CANTON",
        "locality_col": "POBLADO",
        "street_col": "DIRECCION",
        "country_name": "Costa Rica",
    },
    "GTM": {
        "raw_file": "raw/sire_2024_filtrado/sire_2024_filtrado.shp",
        "read_fn": "shapefile",
        "read_kwargs": {"encoding": "latin-1"},
        "field_indices": {"id": 0, "adm1": 1, "adm2": 3, "street": 5},
        "id_col": "código",
        "adm1_col": "departamen",
        "adm2_col": "municipio",
        "locality_col": None,
        "street_col": "dirección",
        "country_name": "Guatemala",
    },
    "GUY": {
        "raw_file": "raw/School Data-Mapping.xlsx",
        "read_fn": "excel",
        "read_kwargs": {},
        "id_col": "School_ID",
        "adm1_col": "Region_No",
        "adm2_col": None,
        "locality_col": None,
        "street_col": "Address",
        "country_name": "Guyana",
    },
    "HND": {
        "raw_file": "raw/SIPLIE_nivel nacional.xlsx",
        "read_fn": "excel",
        "read_kwargs": {"sheet_name": "Detalle", "skiprows": 7},
        "id_col": "Código Centro",
        "adm1_col": "Departamento",
        "adm2_col": "Municipio",
        "locality_col": None,
        "street_col": "DireccionCentro",
        "country_name": "Honduras",
    },
    "MEX": {
        "raw_file": "raw/siged_total.csv",
        "read_fn": "csv",
        "read_kwargs": {"encoding": "utf-8", "low_memory": False},
        "id_col": "id_centro",
        "adm1_col": "nombre_entidad",
        "adm2_col": "nombre_municipio",
        "locality_col": "nombre_localidad",
        "street_col": "domicilio_completo",
        "country_name": "Mexico",
    },
    "PER": {
        "raw_file": "raw/Padron.csv",
        "read_fn": "csv",
        "read_kwargs": {"sep": ";", "encoding": "ISO-8859-1", "low_memory": False},
        "id_col": None,  # composite: COD_MOD + ANEXO
        "id_composite": ("COD_MOD", "ANEXO"),
        "adm1_col": "DPTO",
        "adm2_col": "PROV",
        "locality_col": "LOCALIDAD",
        "street_col": "DIRECCION",
        "extra_cols": ["REFERENCIA", "DIST"],
        "country_name": "Peru",
    },
    "PRY": {
        "raw_file": "raw/establecimientos_2023.csv",
        "read_fn": "csv",
        "read_kwargs": {"encoding": "utf-8", "low_memory": False},
        "id_col": "codigo_establecimiento",
        "adm1_col": "nombre_departamento",
        "adm2_col": "nombre_distrito",
        "locality_col": "nombre_barrio_localidad",
        "street_col": "direccion",
        "country_name": "Paraguay",
    },
    "SLV": {
        "raw_file": "raw/SLV_coord_EDU.csv",
        "read_fn": "csv",
        "read_kwargs": {"encoding": "latin-1"},
        "id_col": None,  # first column (CÓDIGO C.E.) has encoding issues
        "adm1_col": "DEPARTAMENTO",
        "adm2_col": "MUNICIPIO",
        "locality_col": None,
        "street_col": None,
        "country_name": "El Salvador",
    },
    "SUR": {
        "raw_file": "raw/Suriname School List_03202024.xlsx",
        "read_fn": "excel",
        "read_kwargs": {},
        "id_col": "School code",
        "adm1_col": "District",
        "adm2_col": "Ressort",
        "locality_col": "Settlement area",
        "street_col": "Address",
        "country_name": "Suriname",
    },
    "URY": {
        "raw_file": None,  # shapefiles — no separate address file
        "id_col": None,
        "adm1_col": None,
        "adm2_col": None,
        "locality_col": None,
        "street_col": None,
        "country_name": "Uruguay",
        "skip": True,
    },
}


# ===================================================================
# Helper functions
# ===================================================================

def normalize_name(s):
    """Strip accents, control chars, lowercase, trim — for comparing admin unit names."""
    if pd.isna(s) or s is None:
        return ""
    s = str(s).strip().lower()
    # Decompose unicode, strip combining marks (accents) and control chars
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(
        c for c in nfkd
        if not unicodedata.combining(c) and unicodedata.category(c)[0] != "C"
    )


def dms_to_dd(dms_str):
    """Convert DMS string like '25°17'13.5"S' or '25°17\'13.5"S' to decimal degrees."""
    import re
    if pd.isna(dms_str) or dms_str is None:
        return np.nan
    s = str(dms_str).strip()
    if not s:
        return np.nan
    # Try numeric first
    try:
        return float(s)
    except ValueError:
        pass
    # DMS patterns: 25°17'13.5"S or 25°17'13.5"S (various encodings of degree symbol)
    m = re.match(
        r"(-?\d+)[°\xb0\xba\u00ba]?\s*(\d+)['\u2019]?\s*([\d.]+)?[\"″]?\s*([NSEWnsew])?",
        s,
    )
    if not m:
        return np.nan
    deg = float(m.group(1))
    mins = float(m.group(2))
    secs = float(m.group(3)) if m.group(3) else 0.0
    direction = m.group(4).upper() if m.group(4) else ""
    dd = abs(deg) + mins / 60.0 + secs / 3600.0
    if direction in ("S", "W") or deg < 0:
        dd = -dd
    return dd


def load_boundaries():
    """Load ADM1 boundary polygons via pyshp (handles latin-1 encoding)."""
    import shapefile as shp_lib
    from shapely.geometry import shape as shp_shape

    sf = shp_lib.Reader(
        str(BOUNDS_DIR / "level 1" / "lac-level-1.shp"), encoding="latin-1"
    )
    fields = [f[0] for f in sf.fields[1:]]
    records, geoms = [], []
    for i, rec in enumerate(sf.iterRecords()):
        records.append(dict(zip(fields, rec)))
        geoms.append(shp_shape(sf.shape(i).__geo_interface__))

    adm1 = gpd.GeoDataFrame(records, geometry=geoms, crs="EPSG:4326")
    adm1["adm1_norm"] = adm1["ADM1_EN"].apply(normalize_name)
    return adm1


def load_cima(iso):
    """Read the CIMA CSV for a country."""
    path = BASE / iso / "processed" / f"{iso}_total_cima.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, dtype={"id_centro": str})
    df["id_centro"] = df["id_centro"].astype(str).str.strip()
    return df


def extract_addresses(iso, cfg):
    """Read raw file, return DataFrame with id_centro + address columns."""
    if cfg.get("skip"):
        return None

    raw_path = BASE / iso / cfg["raw_file"]
    if not raw_path.exists():
        print(f"    WARNING: raw file not found: {raw_path}")
        return None

    # --- Read raw data ---
    if cfg["read_fn"] == "csv":
        kw = dict(cfg["read_kwargs"])
        if "usecols" in cfg:
            kw["usecols"] = cfg["usecols"]
        # Try multiple encodings; pick the one with fewest garbage chars
        cfg_enc = kw.get("encoding", "utf-8")
        best_df, best_bad = None, float("inf")
        for enc in dict.fromkeys(["utf-8", cfg_enc, "latin-1"]):
            try:
                kw_try = {**kw, "encoding": enc}
                trial = pd.read_csv(raw_path, **kw_try)
                # Count C1 control chars (0x80-0x9F) — sign of wrong encoding
                sample = trial.head(100).to_string()
                bad = sum(1 for c in sample if 0x80 <= ord(c) <= 0x9F)
                if bad < best_bad:
                    best_df, best_bad = trial, bad
                if bad == 0:
                    break
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        df = best_df if best_df is not None else pd.read_csv(raw_path, **kw)
    elif cfg["read_fn"] == "excel":
        df = pd.read_excel(raw_path, **cfg["read_kwargs"])
    elif cfg["read_fn"] == "shapefile":
        import shapefile as shp_lib
        sf = shp_lib.Reader(str(raw_path), **cfg["read_kwargs"])
        flds = [f[0] for f in sf.fields[1:]]
        idx = cfg["field_indices"]
        rows = []
        for rec in sf.iterRecords():
            r = list(rec)
            rows.append({
                "id_centro": str(r[idx["id"]]),
                "raw_adm1": str(r[idx["adm1"]]),
                "raw_adm2": str(r[idx["adm2"]]) if "adm2" in idx else "",
                "raw_street": str(r[idx["street"]]) if "street" in idx else "",
            })
        result = pd.DataFrame(rows)
        result["raw_locality"] = ""
        result["id_centro"] = result["id_centro"].astype(str).str.strip()
        return result
    else:
        return None

    # --- Build id_centro ---
    if cfg.get("id_composite"):
        cols = cfg["id_composite"]
        # Clean BOM from PER column names
        df.columns = [c.replace("ï»¿", "").replace("\ufeff", "").strip() for c in df.columns]
        df["id_centro"] = df[cols[0]].astype(str) + "-" + df[cols[1]].astype(str)
    elif cfg["id_col"] is None:
        # SLV: first column has encoding issues
        df["id_centro"] = df.iloc[:, 0].astype(str).str.strip()
    else:
        col = cfg["id_col"]
        # Handle possible column name encoding issues
        if col not in df.columns:
            col = next((c for c in df.columns if normalize_name(c) == normalize_name(col)), None)
        if col is None:
            print(f"    WARNING: id_col not found in {iso}")
            return None
        df["id_centro"] = df[col].astype(str).str.strip()

    # --- Extract address columns ---
    def safe_col(name):
        if name is None:
            return None
        if name in df.columns:
            return name
        # Fuzzy match for encoding issues
        match = next((c for c in df.columns if normalize_name(c) == normalize_name(name)), None)
        return match

    adm1_c = safe_col(cfg["adm1_col"])
    adm2_c = safe_col(cfg["adm2_col"])
    loc_c = safe_col(cfg.get("locality_col"))
    street_c = safe_col(cfg.get("street_col"))

    result = pd.DataFrame({"id_centro": df["id_centro"]})
    result["raw_adm1"] = df[adm1_c].astype(str).str.strip() if adm1_c else ""
    result["raw_adm2"] = df[adm2_c].astype(str).str.strip() if adm2_c else ""
    result["raw_locality"] = df[loc_c].astype(str).str.strip() if loc_c else ""
    result["raw_street"] = df[street_c].astype(str).str.strip() if street_c else ""

    # Extra cols (PER has REFERENCIA, DIST)
    for ec in cfg.get("extra_cols", []):
        ec_found = safe_col(ec)
        if ec_found:
            result[f"raw_{ec.lower()}"] = df[ec_found].astype(str).str.strip()

    # Clean "nan" strings
    for c in result.columns:
        if c != "id_centro":
            result[c] = result[c].replace({"nan": "", "None": "", "none": ""})

    # Deduplicate by id_centro (take first occurrence)
    result = result.drop_duplicates(subset="id_centro", keep="first")
    return result


# ===================================================================
# Task A: Coordinate validation via spatial join
# ===================================================================

def validate_coordinates(cima, addr_df, boundaries, iso):
    """
    For schools with coords + admin info, check if coords fall in stated admin unit.

    Returns a DataFrame with QC results per school.
    """
    bounds = COUNTRY_BOUNDS.get(iso)
    if bounds is None:
        return pd.DataFrame()

    # Ensure numeric coordinates (handle DMS strings like PRY)
    cima = cima.copy()
    lat_numeric = pd.to_numeric(cima["latitud"], errors="coerce")
    if lat_numeric.notna().sum() == 0 and cima["latitud"].notna().sum() > 0:
        # All non-null values failed numeric parse — try DMS conversion
        cima["latitud"] = cima["latitud"].apply(dms_to_dd)
        cima["longitud"] = cima["longitud"].apply(dms_to_dd)
    else:
        cima["latitud"] = lat_numeric
        cima["longitud"] = pd.to_numeric(cima["longitud"], errors="coerce")

    # Treat (0, 0) as missing — common placeholder for no-data
    zero_mask = (cima["latitud"] == 0) & (cima["longitud"] == 0)
    cima.loc[zero_mask, ["latitud", "longitud"]] = np.nan

    # Filter to schools with valid coordinates
    has_coords = cima["latitud"].notna() & cima["longitud"].notna()
    df = cima[has_coords].copy()
    if df.empty:
        return pd.DataFrame()

    # --- Step 1: Bounding box pre-check ---
    lat_ok = df["latitud"].between(bounds["lat"][0], bounds["lat"][1])
    lon_ok = df["longitud"].between(bounds["lon"][0], bounds["lon"][1])
    df["in_bounds"] = lat_ok & lon_ok

    # --- Step 2: Detect likely swapped lat/lon ---
    # If lon is in lat range and lat is in lon range → likely swapped
    lat_in_lon = df["latitud"].between(bounds["lon"][0], bounds["lon"][1])
    lon_in_lat = df["longitud"].between(bounds["lat"][0], bounds["lat"][1])
    df["likely_swapped"] = (~df["in_bounds"]) & lat_in_lon & lon_in_lat

    # --- Step 3: Merge with address data ---
    if addr_df is not None and not addr_df.empty:
        df = df.merge(
            addr_df[["id_centro", "raw_adm1", "raw_adm2"]],
            on="id_centro", how="left",
        )
    else:
        df["raw_adm1"] = ""
        df["raw_adm2"] = ""

    df["raw_adm1_norm"] = df["raw_adm1"].apply(normalize_name)

    # --- Step 4: Spatial join (only for in-bounds points) ---
    in_bounds_df = df[df["in_bounds"]].copy()
    if in_bounds_df.empty:
        df["polygon_adm1"] = ""
        df["polygon_adm1_norm"] = ""
    else:
        # Filter boundaries to this country
        country_bounds = boundaries[boundaries["ADM0_PCODE"] == iso].copy()
        if country_bounds.empty:
            df["polygon_adm1"] = ""
            df["polygon_adm1_norm"] = ""
        else:
            geometry = [
                Point(lon, lat)
                for lon, lat in zip(in_bounds_df["longitud"], in_bounds_df["latitud"])
            ]
            gdf = gpd.GeoDataFrame(
                in_bounds_df[["id_centro"]],
                geometry=geometry,
                crs="EPSG:4326",
            )
            joined = gpd.sjoin(gdf, country_bounds, how="left", predicate="within")
            # Take first match per school (some boundary overlaps)
            joined = joined.drop_duplicates(subset="id_centro", keep="first")
            joined = joined[["id_centro", "ADM1_EN", "adm1_norm"]].rename(
                columns={"ADM1_EN": "polygon_adm1", "adm1_norm": "polygon_adm1_norm"}
            )
            df = df.merge(joined, on="id_centro", how="left")

    # Fill missing polygon columns
    for c in ["polygon_adm1", "polygon_adm1_norm"]:
        if c not in df.columns:
            df[c] = ""
    df["polygon_adm1"] = df["polygon_adm1"].fillna("")
    df["polygon_adm1_norm"] = df["polygon_adm1_norm"].fillna("")

    # --- Step 5: Assign QC status ---
    aliases = ADM1_ALIASES.get(iso, {})

    def assign_status(row):
        if row["likely_swapped"]:
            return "LIKELY_SWAPPED"
        if not row["in_bounds"]:
            return "OUT_OF_BOUNDS"
        if row["polygon_adm1_norm"] == "":
            return "NO_POLYGON"
        if row["raw_adm1_norm"] == "":
            return "NO_RAW_ADM"
        raw_n = row["raw_adm1_norm"]
        poly_n = row["polygon_adm1_norm"]
        # Apply known aliases
        raw_n = aliases.get(raw_n, raw_n)
        if raw_n == poly_n:
            return "MATCH"
        # Partial match: check if one contains the other
        if raw_n in poly_n or poly_n in raw_n:
            return "MATCH"
        return "MISMATCH"

    df["qc_status"] = df.apply(assign_status, axis=1)

    # Build output
    result = df[[
        "id_centro", "nombre_centro", "latitud", "longitud",
        "raw_adm1", "raw_adm2", "polygon_adm1", "qc_status",
    ]].copy()
    result.insert(0, "iso", iso)
    return result


# ===================================================================
# Task A2: Duplicate coordinates check
# ===================================================================

def check_duplicate_coordinates(cima, addr_df, iso):
    """
    Two checks:
    1. Schools sharing exact same coordinates (any).
    2. Schools sharing coords but with DIFFERENT addresses (suspicious).

    Returns: (dup_df, n_with_coords, n_dup_all, n_dup_diff_addr)
    """
    cima = cima.copy()
    cima["latitud"] = pd.to_numeric(cima["latitud"], errors="coerce")
    cima["longitud"] = pd.to_numeric(cima["longitud"], errors="coerce")

    has_coords = cima["latitud"].notna() & cima["longitud"].notna()
    df = cima[has_coords].copy()
    if df.empty:
        return pd.DataFrame(), 0, 0, 0

    # Merge address info
    has_addr = False
    if addr_df is not None and not addr_df.empty:
        addr_cols = ["id_centro", "raw_adm1", "raw_adm2", "raw_locality", "raw_street"]
        available = [c for c in addr_cols if c in addr_df.columns]
        df = df.merge(addr_df[available], on="id_centro", how="left")
        has_addr = "raw_street" in df.columns or "raw_adm2" in df.columns

    # Round coords to 5 decimals (~1m precision)
    df["lat_r"] = df["latitud"].round(5)
    df["lon_r"] = df["longitud"].round(5)

    # Groups with >1 school at same location
    coord_counts = df.groupby(["lat_r", "lon_r"]).size().reset_index(name="n_schools")
    dup_coords = coord_counts[coord_counts["n_schools"] > 1]

    if dup_coords.empty:
        return pd.DataFrame(), len(df), 0, 0

    dup_df = df.merge(dup_coords[["lat_r", "lon_r", "n_schools"]], on=["lat_r", "lon_r"])
    n_dup_all = len(dup_df)

    # --- Check 2: same coords, different address ---
    n_dup_diff_addr = 0
    dup_df["diff_addr"] = False
    if has_addr:
        # Build a comparable address string per school
        addr_parts = []
        for c in ["raw_street", "raw_adm2", "raw_locality"]:
            if c in dup_df.columns:
                addr_parts.append(dup_df[c].fillna("").astype(str).str.strip().str.lower())
        if addr_parts:
            dup_df["_addr_key"] = addr_parts[0]
            for p in addr_parts[1:]:
                dup_df["_addr_key"] = dup_df["_addr_key"] + "|" + p

            # For each coord group, check if there are >1 distinct addresses
            addr_variety = dup_df.groupby(["lat_r", "lon_r"])["_addr_key"].nunique().reset_index(
                name="n_distinct_addr"
            )
            diff_addr_locs = addr_variety[addr_variety["n_distinct_addr"] > 1][["lat_r", "lon_r"]]

            if not diff_addr_locs.empty:
                dup_df = dup_df.merge(diff_addr_locs, on=["lat_r", "lon_r"], how="left", indicator=True)
                dup_df["diff_addr"] = dup_df["_merge"] == "both"
                dup_df.drop(columns=["_merge"], inplace=True)
                n_dup_diff_addr = dup_df["diff_addr"].sum()

            dup_df.drop(columns=["_addr_key"], inplace=True)

    # Build output
    out_cols = ["id_centro", "nombre_centro", "latitud", "longitud",
                "n_schools", "diff_addr"]
    for c in ["raw_adm1", "raw_adm2", "raw_locality", "raw_street"]:
        if c in dup_df.columns:
            out_cols.append(c)
    result = dup_df[out_cols].copy()
    result.insert(0, "iso", iso)

    return result, len(df), n_dup_all, n_dup_diff_addr


# ===================================================================
# Task B: Geocode missing coordinates
# ===================================================================

def geocode_missing(cima, addr_df, iso, cfg, geocoder, cache):
    """
    For schools without coordinates, attempt geocoding via Nominatim.

    Returns DataFrame with geocoded results.
    """
    if addr_df is None or addr_df.empty:
        return pd.DataFrame()

    # Filter to schools missing coordinates
    missing = cima[cima["latitud"].isna() | cima["longitud"].isna()].copy()
    if missing.empty:
        return pd.DataFrame()

    # Merge with address data
    missing = missing.merge(addr_df, on="id_centro", how="left")
    country = cfg["country_name"]

    results = []
    for _, row in missing.iterrows():
        street = row.get("raw_street", "")
        locality = row.get("raw_locality", "")
        adm2 = row.get("raw_adm2", "")
        adm1 = row.get("raw_adm1", "")

        # Build queries from most to least specific
        queries = []
        if street:
            queries.append((f"{street}, {adm2}, {adm1}, {country}", "STREET"))
        if locality:
            queries.append((f"{locality}, {adm2}, {adm1}, {country}", "LOCALITY"))
        if adm2:
            queries.append((f"{adm2}, {adm1}, {country}", "ADM2"))
        # Skip ADM1-only (too coarse — project rule: no centroids)

        if not queries:
            results.append({
                "iso": iso,
                "id_centro": row["id_centro"],
                "nombre_centro": row.get("nombre_centro", ""),
                "geocoded_lat": np.nan,
                "geocoded_lon": np.nan,
                "geocode_query": "",
                "geocode_level": "SKIPPED_NO_ADDRESS",
                "nominatim_display": "",
            })
            continue

        geocoded = False
        for query, level in queries:
            query_clean = query.strip(", ")
            # Check cache first
            if query_clean in cache:
                cached = cache[query_clean]
                if cached is not None:
                    results.append({
                        "iso": iso,
                        "id_centro": row["id_centro"],
                        "nombre_centro": row.get("nombre_centro", ""),
                        "geocoded_lat": cached["lat"],
                        "geocoded_lon": cached["lon"],
                        "geocode_query": query_clean,
                        "geocode_level": f"SUCCESS_{level}",
                        "nominatim_display": cached.get("display", ""),
                    })
                    geocoded = True
                    break
                else:
                    continue  # cached failure, try next level

            # Query Nominatim
            if geocoder is None:
                continue
            try:
                location = geocoder.geocode(query_clean)
                if location:
                    cache[query_clean] = {
                        "lat": location.latitude,
                        "lon": location.longitude,
                        "display": location.address,
                    }
                    results.append({
                        "iso": iso,
                        "id_centro": row["id_centro"],
                        "nombre_centro": row.get("nombre_centro", ""),
                        "geocoded_lat": location.latitude,
                        "geocoded_lon": location.longitude,
                        "geocode_query": query_clean,
                        "geocode_level": f"SUCCESS_{level}",
                        "nominatim_display": location.address,
                    })
                    geocoded = True
                    break
                else:
                    cache[query_clean] = None  # mark as failed
            except Exception as e:
                print(f"      Geocode error for {row['id_centro']}: {e}")
                cache[query_clean] = None

        if not geocoded:
            results.append({
                "iso": iso,
                "id_centro": row["id_centro"],
                "nombre_centro": row.get("nombre_centro", ""),
                "geocoded_lat": np.nan,
                "geocoded_lon": np.nan,
                "geocode_query": queries[0][0] if queries else "",
                "geocode_level": "FAILED",
                "nominatim_display": "",
            })

    return pd.DataFrame(results)


# ===================================================================
# Main
# ===================================================================

def main():
    parser = argparse.ArgumentParser(description="QC and geocode school coordinates")
    parser.add_argument("--qc-only", action="store_true", help="Run QC validation only")
    parser.add_argument("--countries", nargs="*", help="Process specific countries (ISO codes)")
    args = parser.parse_args()

    print("=" * 65)
    print("Coordinate QC & Gap-Filling")
    print("=" * 65)

    # --- Load boundaries ---
    print("\nLoading admin boundaries...")
    boundaries = load_boundaries()
    print(f"  ADM1: {len(boundaries)} polygons")

    # --- Load geocode cache ---
    cache = {}
    if GEOCODE_CACHE_PATH.exists():
        with open(GEOCODE_CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
        print(f"  Geocode cache: {len(cache)} entries loaded")

    # --- Init geocoder ---
    geocoder = None
    if not args.qc_only:
        try:
            from geopy.geocoders import Nominatim
            from geopy.extra.rate_limiter import RateLimiter
            _nom = Nominatim(user_agent="idb_school_accessibility_platform_qc")
            geocoder = RateLimiter(_nom.geocode, min_delay_seconds=1.1)
            print("  Nominatim geocoder ready")
        except ImportError:
            print("  WARNING: geopy not installed — geocoding disabled")
            print("  Install with: uv pip install geopy")

    # --- Select countries ---
    countries = args.countries if args.countries else list(COUNTRY_CONFIG.keys())

    # --- Process ---
    all_qc = []
    all_dups = []
    all_geocoded = []
    summary_rows = []

    print()
    for iso in countries:
        cfg = COUNTRY_CONFIG.get(iso)
        if cfg is None:
            print(f"  {iso}: not in COUNTRY_CONFIG, skipping")
            continue
        if cfg.get("skip"):
            print(f"  {iso}: skipped (no address file)")
            continue

        print(f"  {iso} ({cfg['country_name']})")

        # Load CIMA
        cima = load_cima(iso)
        if cima is None or cima.empty:
            print(f"    No CIMA file found")
            continue

        total = len(cima)
        has_coords = (cima["latitud"].notna() & cima["longitud"].notna()).sum()
        missing_coords = total - has_coords
        print(f"    Schools: {total:,} total, {has_coords:,} with coords, {missing_coords:,} missing")

        # Extract addresses
        addr = extract_addresses(iso, cfg)
        if addr is not None:
            print(f"    Addresses: {len(addr):,} extracted from raw")

        # --- Task A: QC validation ---
        qc = validate_coordinates(cima, addr, boundaries, iso)
        if not qc.empty:
            all_qc.append(qc)
            match = (qc["qc_status"] == "MATCH").sum()
            mismatch = (qc["qc_status"] == "MISMATCH").sum()
            oob = (qc["qc_status"] == "OUT_OF_BOUNDS").sum()
            swapped = (qc["qc_status"] == "LIKELY_SWAPPED").sum()
            no_poly = (qc["qc_status"] == "NO_POLYGON").sum()
            no_adm = (qc["qc_status"] == "NO_RAW_ADM").sum()
            checked = len(qc)
            match_rate = match / max(checked - no_adm, 1) * 100

            print(f"    QC: {match:,} match, {mismatch:,} mismatch, "
                  f"{oob:,} out-of-bounds, {swapped:,} swapped, "
                  f"{no_poly:,} no-polygon, {no_adm:,} no-adm | "
                  f"rate={match_rate:.1f}%")

            summary_rows.append({
                "iso": iso,
                "total": total,
                "with_coords": has_coords,
                "missing_coords": missing_coords,
                "qc_checked": checked,
                "match": match,
                "mismatch": mismatch,
                "out_of_bounds": oob,
                "likely_swapped": swapped,
                "no_polygon": no_poly,
                "no_raw_adm": no_adm,
                "match_rate_pct": round(match_rate, 1),
            })

        # --- Task A2: Duplicate coordinates ---
        dup_result, n_with_coords, n_dup_all, n_dup_diff = check_duplicate_coordinates(cima, addr, iso)
        if not dup_result.empty:
            all_dups.append(dup_result)
            dup_all_pct = n_dup_all / max(n_with_coords, 1) * 100
            dup_diff_pct = n_dup_diff / max(n_with_coords, 1) * 100
            print(f"    Dup coords: {n_dup_all:,} same location ({dup_all_pct:.1f}%), "
                  f"{n_dup_diff:,} different address ({dup_diff_pct:.1f}%)")
        else:
            n_dup_all = n_dup_diff = 0
            dup_all_pct = dup_diff_pct = 0.0

        # Add dup info to summary
        if summary_rows and summary_rows[-1]["iso"] == iso:
            summary_rows[-1]["dup_coord_schools"] = n_dup_all
            summary_rows[-1]["dup_coord_pct"] = round(dup_all_pct, 1)
            summary_rows[-1]["dup_diff_addr"] = n_dup_diff
            summary_rows[-1]["dup_diff_addr_pct"] = round(dup_diff_pct, 1)

        # --- Task B: Geocode missing ---
        if not args.qc_only and missing_coords > 0:
            geo = geocode_missing(cima, addr, iso, cfg, geocoder, cache)
            if not geo.empty:
                all_geocoded.append(geo)
                success = geo["geocode_level"].str.startswith("SUCCESS").sum()
                failed = (geo["geocode_level"] == "FAILED").sum()
                skipped = geo["geocode_level"].str.startswith("SKIPPED").sum()
                print(f"    Geocoded: {success:,} success, {failed:,} failed, {skipped:,} skipped")

                # Save cache periodically
                with open(GEOCODE_CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)

    # --- Export reports ---
    print("\n" + "=" * 65)
    print("EXPORTING REPORTS")
    print("=" * 65)

    if all_qc:
        qc_df = pd.concat(all_qc, ignore_index=True)
        qc_df.to_csv(RESULTS / "qc_coordinate_report.csv", index=False, encoding="utf-8")
        print(f"  {RESULTS / 'qc_coordinate_report.csv'}: {len(qc_df):,} rows")

    if summary_rows:
        sum_df = pd.DataFrame(summary_rows)
        sum_df.to_csv(RESULTS / "qc_coordinate_summary.csv", index=False, encoding="utf-8")
        print(f"  {RESULTS / 'qc_coordinate_summary.csv'}: {len(sum_df)} countries")

    if all_dups:
        dup_df = pd.concat(all_dups, ignore_index=True)
        dup_df.to_csv(RESULTS / "qc_duplicate_coordinates.csv", index=False, encoding="utf-8")
        print(f"  {RESULTS / 'qc_duplicate_coordinates.csv'}: {len(dup_df):,} rows")

    if all_geocoded:
        geo_df = pd.concat(all_geocoded, ignore_index=True)
        geo_df.to_csv(RESULTS / "geocoded_coordinates.csv", index=False, encoding="utf-8")
        print(f"  {RESULTS / 'geocoded_coordinates.csv'}: {len(geo_df):,} rows")

    # Save final cache
    with open(GEOCODE_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"  {GEOCODE_CACHE_PATH}: {len(cache)} entries")

    # --- Print summary table ---
    if summary_rows:
        print("\n" + "=" * 65)
        print("QC SUMMARY")
        print("=" * 65)
        print(f"{'ISO':<5} {'Total':>8} {'Match%':>7} {'Mis':>5} {'OOB':>5} "
              f"{'DupAll':>8} {'DifAddr':>8}")
        print("-" * 55)
        for s in summary_rows:
            da = s.get('dup_coord_schools', 0)
            da_p = s.get('dup_coord_pct', 0.0)
            dd = s.get('dup_diff_addr', 0)
            dd_p = s.get('dup_diff_addr_pct', 0.0)
            print(f"{s['iso']:<5} {s['total']:>8,} {s['match_rate_pct']:>6.1f}% "
                  f"{s['mismatch']:>5,} {s['out_of_bounds']:>5,} "
                  f"{da:>5,}({da_p:>2.0f}%) {dd:>5,}({dd_p:>2.0f}%)")

    print("\nDone.")


if __name__ == "__main__":
    main()
