"""
Phase B-1: Geocode schools missing coordinates or with coordinate-address mismatches.

Targets:
  - Schools with no coordinates (latitud is NaN)
  - Schools at (0,0) — treated as missing
  - Schools flagged as MISMATCH or OUT_OF_BOUNDS in QC
  - Schools with duplicate coordinates but different addresses

Geocoder cascade: ArcGIS → Photon → Nominatim (all free, no API key).

Must be run from project root:
    uv run python pipeline/05_geocode_missing.py --dry-run
    uv run python pipeline/05_geocode_missing.py --countries MEX
    uv run python pipeline/05_geocode_missing.py
"""

import argparse
import json
import sys
import time
from math import radians, sin, cos, asin, sqrt
from pathlib import Path

import unicodedata

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path("data/schools/AR")
RESULTS = Path("results")
QC_REPORT = RESULTS / "qc_coordinate_report.csv"
QC_DUPES = RESULTS / "qc_duplicate_coordinates.csv"
CACHE_PATH = RESULTS / "geocode_cache.json"

# Countries with street-level addresses (Phase B-1)
# Reuses COUNTRY_CONFIG from 02_qc_coordinates.py via import
PHASE_B1_ISOS = [
    "MEX", "BRA", "COL", "ARG", "HND", "PRY", "GTM",
    "CRI", "PER", "BLZ", "BOL", "GUY", "SUR", "CHL",
]

# Country bounding boxes for geocode validation (lat_min, lat_max, lon_min, lon_max)
COUNTRY_BBOX = {
    "ARG": (-56, -21, -74, -53), "BLZ": (15, 19, -90, -87),
    "BOL": (-23, -9, -70, -57),  "BRA": (-34, 6, -74, -32),
    "BRB": (13, 14, -60, -59),   "CHL": (-56, -17, -76, -66),
    "COL": (-5, 14, -82, -66),   "CRI": (8, 12, -86, -82),
    "DOM": (17, 20, -72, -68),   "ECU": (-5, 2, -92, -75),
    "GTM": (13, 18, -93, -88),   "GUY": (1, 9, -62, -56),
    "HND": (13, 17, -90, -83),   "JAM": (17, 19, -79, -76),
    "MEX": (14, 33, -118, -86),  "PAN": (7, 10, -83, -77),
    "PER": (-19, 0, -82, -68),   "PRY": (-28, -19, -63, -54),
    "SLV": (13, 15, -91, -87),   "SUR": (1, 6, -59, -53),
    "URY": (-35, -30, -59, -53),
}


# ---------------------------------------------------------------------------
# Geocoder setup
# ---------------------------------------------------------------------------

def setup_geocoders():
    """Initialize geocoder cascade: ArcGIS → Photon → Nominatim."""
    from geopy.geocoders import ArcGIS, Photon, Nominatim
    from geopy.extra.rate_limiter import RateLimiter

    geocoders = []

    try:
        _arc = ArcGIS(user_agent="idb_school_accessibility")
        geocoders.append(("arcgis", RateLimiter(_arc.geocode, min_delay_seconds=0.3)))
    except Exception as e:
        print(f"  ArcGIS init failed: {e}")

    try:
        _pho = Photon(user_agent="idb_school_accessibility")
        geocoders.append(("photon", RateLimiter(_pho.geocode, min_delay_seconds=0.35)))
    except Exception as e:
        print(f"  Photon init failed: {e}")

    try:
        _nom = Nominatim(user_agent="idb_school_accessibility_phase_b")
        geocoders.append(("nominatim", RateLimiter(_nom.geocode, min_delay_seconds=1.1)))
    except Exception as e:
        print(f"  Nominatim init failed: {e}")

    return geocoders


# ---------------------------------------------------------------------------
# Target identification
# ---------------------------------------------------------------------------

def _detect_centroids_in_coords(cima, addr_df, threshold=5):
    """Detect schools whose coordinates are likely municipal centroids.

    Returns set of id_centro for schools at shared points (>=threshold)
    where addresses are genuinely different (not same building).
    """
    georef = cima[cima["latitud"].notna() & cima["longitud"].notna()].copy()
    if georef.empty:
        return set()

    georef["geo_key"] = (
        georef["latitud"].round(3).astype(str) + "," +
        georef["longitud"].round(3).astype(str)
    )
    point_counts = georef.groupby("geo_key")["id_centro"].count()
    shared_points = set(point_counts[point_counts >= threshold].index)
    if not shared_points:
        return set()

    candidates = georef[georef["geo_key"].isin(shared_points)].copy()

    # Filter: only include if addresses are genuinely different (not same building)
    # Same building = same street + same municipality at that point
    if addr_df is not None and not addr_df.empty:
        candidates = candidates.merge(
            addr_df[["id_centro", "raw_street", "raw_adm2"]],
            on="id_centro", how="left",
        )
        same_building_ids = set()
        for geo_key, group in candidates.groupby("geo_key"):
            streets = group["raw_street"].fillna("").str.lower().str.strip().unique()
            adm2s = group["raw_adm2"].fillna("").str.lower().str.strip().unique()
            streets = [s for s in streets if s and s not in ("nan", "none", "")]
            adm2s = [a for a in adm2s if a and a not in ("nan", "none", "")]
            if len(adm2s) <= 1 and len(streets) <= 1:
                same_building_ids |= set(group["id_centro"])

        return set(candidates["id_centro"]) - same_building_ids
    else:
        return set(candidates["id_centro"])


def identify_targets(iso, addr_df=None):
    """Identify all schools needing geocoding for a country."""
    cima_path = BASE / iso / "processed" / f"{iso}_total_cima.csv"
    if not cima_path.exists():
        return pd.DataFrame(), set(), set(), set(), set(), set()

    cima = pd.read_csv(cima_path, dtype={"id_centro": str})

    # 1. Missing coords
    missing = set(cima[cima["latitud"].isna()]["id_centro"])

    # 2. Zero coords — either lat or lon is zero (partial zeros are also invalid)
    zeros = set(cima[(cima["latitud"] == 0) | (cima["longitud"] == 0)]["id_centro"])

    # 3. QC mismatches + OOB
    mismatches = set()
    if QC_REPORT.exists():
        qc = pd.read_csv(QC_REPORT, dtype={"id_centro": str})
        qc_iso = qc[qc["iso"] == iso]
        mismatches = set(qc_iso[qc_iso["qc_status"].isin(["MISMATCH", "OUT_OF_BOUNDS"])]["id_centro"])

    # 4. Duplicate coords with different addresses (from QC report)
    dup_addr = set()
    if QC_DUPES.exists():
        dupes = pd.read_csv(QC_DUPES, dtype={"id_centro": str})
        dupes_iso = dupes[(dupes["iso"] == iso) & (dupes["diff_addr"] == True)]
        dup_addr = set(dupes_iso["id_centro"])

    # 5. Centroid detection on ALL coords (original + geocoded)
    #    Schools at shared points (>=5) with genuinely different addresses
    #    Excludes same-building (same street + same municipality)
    coord_centroids = _detect_centroids_in_coords(cima, addr_df, threshold=5)

    return cima, missing, zeros, mismatches, dup_addr, coord_centroids


# ---------------------------------------------------------------------------
# Address loading (reuse COUNTRY_CONFIG from 02_qc_coordinates)
# ---------------------------------------------------------------------------

def load_country_config():
    """Import COUNTRY_CONFIG and extract_addresses from 02_qc_coordinates."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("qc_mod", "pipeline/02_qc_coordinates.py")
    qc_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qc_module)
    return qc_module.COUNTRY_CONFIG, qc_module.extract_addresses


# ---------------------------------------------------------------------------
# Geocoding
# ---------------------------------------------------------------------------

def haversine_km(lat1, lon1, lat2, lon2):
    """Distance in km between two points."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def _normalize_admin(s):
    if pd.isna(s): return ""
    s = str(s).lower().strip()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _admin_match(declared, found):
    d, f = _normalize_admin(declared), _normalize_admin(found)
    if not d or not f: return "NO_DATA"
    if d == f: return "MATCH"
    # Partial match: only if the shorter string is >80% of the longer one.
    # Prevents "santander" matching "norte de santander" or "cauca" matching "valle del cauca".
    if d in f or f in d:
        ratio = min(len(d), len(f)) / max(len(d), len(f))
        if ratio > 0.8:
            return "PARTIAL"
    return "MISMATCH"


# Cache for admin boundaries (loaded once per session)
_adm1_cache = {}
_adm2_cache = {}

def _load_admin_boundaries(iso):
    """Load admin boundaries for a country. Cached per session."""
    if iso in _adm1_cache:
        return _adm1_cache[iso], _adm2_cache.get(iso)

    adm1_path = Path("data/bounderys/LAC/level 1/lac-level-1.shp")
    adm2_path = Path("data/bounderys/LAC/level 2/lac-level-2.shp")

    adm1, adm2 = None, None
    if adm1_path.exists():
        all_adm1 = gpd.read_file(adm1_path)
        adm1 = all_adm1[all_adm1["ADM0_PCODE"] == iso]
        _adm1_cache[iso] = adm1
    if adm2_path.exists():
        all_adm2 = gpd.read_file(adm2_path)
        adm2 = all_adm2[all_adm2["ADM0_PCODE"] == iso]
        _adm2_cache[iso] = adm2
    return adm1, adm2


def validate_geocoded(results_df, addr_df, iso):
    """Spatial validation: check if geocoded coords fall in declared admin unit.

    Adds columns: geocoded_in_adm1, geocoded_in_adm2, adm1_check, adm2_check, acceptance.

    Acceptance levels:
      ACCEPT — correct municipality + street/school_name precision
      ACCEPT_WITH_FLAG — correct department but wrong municipality, or admin precision
      REJECT — wrong department, centroid, or outside country
    """
    valid = results_df[results_df["geocoded_lat"].notna()].copy()
    if valid.empty:
        for col in ["geocoded_in_adm1", "geocoded_in_adm2", "adm1_check", "adm2_check", "acceptance"]:
            results_df[col] = ""
        return results_df

    # Merge declared address
    if addr_df is not None:
        valid = valid.merge(addr_df[["id_centro", "raw_adm1", "raw_adm2"]], on="id_centro", how="left")
    else:
        valid["raw_adm1"] = ""
        valid["raw_adm2"] = ""

    # Spatial join
    adm1, adm2 = _load_admin_boundaries(iso)

    # --- Validate GEOCODED coordinates ---
    geo_gdf = gpd.GeoDataFrame(
        valid[["id_centro"]],
        geometry=[Point(lon, lat) for lon, lat in zip(valid["geocoded_lon"], valid["geocoded_lat"])],
        crs="EPSG:4326",
    )

    valid["geocoded_in_adm1"] = ""
    valid["geocoded_in_adm2"] = ""

    if adm1 is not None and not adm1.empty:
        j1 = gpd.sjoin(geo_gdf, adm1[["ADM1_EN", "geometry"]], how="left", predicate="within")
        j1 = j1[~j1.index.duplicated(keep="first")]  # guard against boundary overlaps
        valid["geocoded_in_adm1"] = j1["ADM1_EN"].values

    if adm2 is not None and not adm2.empty:
        j2 = gpd.sjoin(geo_gdf, adm2[["ADM2_EN", "geometry"]], how="left", predicate="within")
        j2 = j2[~j2.index.duplicated(keep="first")]
        valid["geocoded_in_adm2"] = j2["ADM2_EN"].values

    valid["geo_adm1_check"] = valid.apply(lambda r: _admin_match(r.get("raw_adm1"), r["geocoded_in_adm1"]), axis=1)
    valid["geo_adm2_check"] = valid.apply(lambda r: _admin_match(r.get("raw_adm2"), r["geocoded_in_adm2"]), axis=1)

    # --- Validate ORIGINAL coordinates (for compare targets) ---
    valid["original_in_adm1"] = ""
    valid["original_in_adm2"] = ""
    valid["orig_adm1_check"] = "NO_DATA"
    valid["orig_adm2_check"] = "NO_DATA"

    has_orig = valid["original_lat"].notna() & (valid["original_lat"] != 0)
    if has_orig.any():
        orig_gdf = gpd.GeoDataFrame(
            valid.loc[has_orig, ["id_centro"]],
            geometry=[Point(lon, lat) for lon, lat in
                      zip(valid.loc[has_orig, "original_lon"], valid.loc[has_orig, "original_lat"])],
            crs="EPSG:4326",
        )
        if adm1 is not None and not adm1.empty:
            oj1 = gpd.sjoin(orig_gdf, adm1[["ADM1_EN", "geometry"]], how="left", predicate="within")
            oj1 = oj1[~oj1.index.duplicated(keep="first")]
            valid.loc[has_orig, "original_in_adm1"] = oj1["ADM1_EN"].values

        if adm2 is not None and not adm2.empty:
            oj2 = gpd.sjoin(orig_gdf, adm2[["ADM2_EN", "geometry"]], how="left", predicate="within")
            oj2 = oj2[~oj2.index.duplicated(keep="first")]
            valid.loc[has_orig, "original_in_adm2"] = oj2["ADM2_EN"].values

        valid.loc[has_orig, "orig_adm1_check"] = valid.loc[has_orig].apply(
            lambda r: _admin_match(r.get("raw_adm1"), r["original_in_adm1"]), axis=1).values
        valid.loc[has_orig, "orig_adm2_check"] = valid.loc[has_orig].apply(
            lambda r: _admin_match(r.get("raw_adm2"), r["original_in_adm2"]), axis=1).values

    # --- Decision: accept or reject geocoded coordinates ---
    #
    # Rules (validated by ground truth analysis of 550 schools, 11 countries):
    #   - Precision already reclassified by ArcGIS score in geocode_school():
    #       score >= 95 → "street"    (87% within 5km of real location)
    #       score 90-95 → "centroid"  (51% within 5km — municipal centroid)
    #       score < 90  → "uncertain" (only 40% within 5km — unreliable)
    #
    #   - FILL targets (no GPS): accept street + centroid, reject uncertain
    #   - COMPARE targets (has GPS): NEVER replace GPS. Only diagnose discrepancy.
    #     Ground truth showed geocoder median error 4-8km even for known-good schools.
    #     No IMPROVEMENT category — geocoder cannot reliably improve ministry GPS.
    #
    # See: results/geocoder_ground_truth_all_countries.csv (evidence)
    #      results/geocoder_ground_truth_score_analysis.csv (score thresholds)
    def _decide(r):
        prec = str(r.get("geocode_precision", ""))
        target = r.get("target_type", "")

        # Geocoded admin checks
        ga1, ga2 = r["geo_adm1_check"], r["geo_adm2_check"]
        geo_in_muni = ga2 in ("MATCH", "PARTIAL")
        geo_in_dept = ga1 in ("MATCH", "PARTIAL")

        # Always reject: geocoded in wrong department
        if ga1 == "MISMATCH":
            return "REJECT"

        # Uncertain precision (score < 90): reject for all targets
        if prec == "uncertain":
            if target == "fill":
                return "REJECT"
            else:
                return "FLAG"  # keep GPS, flag discrepancy in QC

        # --- FILL targets (no original coord) ---
        if target == "fill":
            if prec == "street" and geo_in_muni:
                return "ACCEPT"              # high confidence
            if prec == "street" and geo_in_dept:
                return "ACCEPT_WITH_FLAG"    # right dept, wrong muni
            if prec == "centroid" and geo_in_muni:
                return "ACCEPT_CENTROID"     # centroid in right muni
            if prec == "centroid" and geo_in_dept:
                return "ACCEPT_CENTROID"     # centroid in right dept
            return "REJECT"

        # --- COMPARE targets (has GPS) ---
        # Never replace GPS. Only diagnose address-vs-coordinate discrepancy.
        oa2 = r["orig_adm1_check"]
        orig_in_muni = r["orig_adm2_check"] in ("MATCH", "PARTIAL")

        if orig_in_muni:
            return "KEEP_ORIGINAL"  # GPS confirmed in correct municipality
        else:
            return "FLAG"           # GPS doesn't match declared address — flag for QC

    valid["acceptance"] = valid.apply(_decide, axis=1)

    # Merge back
    merge_cols = [
        "geocoded_in_adm1", "geocoded_in_adm2", "geo_adm1_check", "geo_adm2_check",
        "original_in_adm1", "original_in_adm2", "orig_adm1_check", "orig_adm2_check",
        "acceptance",
    ]
    results_df = results_df.merge(valid[["id_centro"] + merge_cols], on="id_centro", how="left")
    for col in merge_cols:
        results_df[col] = results_df[col].fillna("")

    return results_df


_JUNK_VALUES = {"", "nan", "none", "ninguno", "s/n", "sin nombre", "sin direccion",
                "ninguno ninguno 0, ninguno", "no disponible", "no aplica", "s/d"}

# Prefixes that indicate the name is a TYPE, not a specific institution.
# "Colegio La Salle" is specific; "Escuela Rural Mixta La Pradera" is not
# because geocoders index named institutions, not generic rural schools.
_GENERIC_PREFIXES = (
    "escuela nueva", "escuela rural mixta", "escuela rural", "escuela urbana",
    "escuela", "centro educativo rural", "centro educativo",
    "sede ", "sede principal", "e m e f", "e m e i f", "e m e i",
    "unidad educativa", "nucleo educativo",
)

# Prefixes that suggest a named, findable institution
_NAMED_PREFIXES = (
    "colegio ", "liceo ", "instituto ", "gimnasio ", "seminario ",
    "fundacion ", "corporacion ", "academia ", "politecnico ",
)


def _is_specific_name(name):
    """Check if a school name is specific enough to geocode by name.

    Only returns True for names likely indexed in geocoder databases:
    named institutions (Colegio X, Liceo Y, Instituto Z), not generic
    types (Escuela Rural, Sede, Centro Educativo).
    """
    if not name or len(name) < 8:
        return False
    name_lower = name.lower().strip()
    # Explicitly named institutions — always usable
    for prefix in _NAMED_PREFIXES:
        if name_lower.startswith(prefix) and len(name_lower) > len(prefix) + 3:
            return True
    # Generic prefixes — never usable
    for prefix in _GENERIC_PREFIXES:
        if name_lower.startswith(prefix):
            return False
    # "Institucion/Institución Educativa [specific name]" — usable if name part is long
    if ("institucion educativa" in name_lower or "institución educativa" in name_lower) and len(name_lower) > 30:
        return True
    # Everything else: skip (single words, indigenous names — too ambiguous for geocoder)
    return False


def build_queries(row, country_name):
    """Build geocoding queries from most to least specific."""
    street = str(row.get("raw_street", "")).strip()
    locality = str(row.get("raw_locality", "")).strip()
    adm2 = str(row.get("raw_adm2", "")).strip()
    adm1 = str(row.get("raw_adm1", "")).strip()
    nombre = str(row.get("nombre_centro", "")).strip()

    # Clean empty/nan/placeholder values
    street = "" if street.lower() in _JUNK_VALUES else street
    locality = "" if locality.lower() in _JUNK_VALUES else locality
    adm2 = "" if adm2.lower() in _JUNK_VALUES else adm2
    adm1 = "" if adm1.lower() in _JUNK_VALUES else adm1
    nombre = "" if nombre.lower() in _JUNK_VALUES else nombre

    queries = []
    # 1. Street address + municipality + department (most precise)
    if street and adm2 and adm1:
        queries.append((f"{street}, {adm2}, {adm1}, {country_name}", "street"))
    # 2. School name + municipality + department (if name is specific)
    if nombre and adm2 and adm1 and _is_specific_name(nombre):
        queries.append((f"{nombre}, {adm2}, {adm1}, {country_name}", "school_name"))
    # 3. Locality + municipality + department
    if locality and adm2 and adm1:
        queries.append((f"{locality}, {adm2}, {adm1}, {country_name}", "locality"))
    # 4. Municipality + department (admin centroid — last resort)
    if adm2 and adm1:
        queries.append((f"{adm2}, {adm1}, {country_name}", "admin"))
    # Skip adm1-only (too coarse) and adm2-only (ambiguous: same municipality name in multiple departments)
    return queries


def _score_to_precision(score, query_precision):
    """Reclassify geocode precision based on ArcGIS score.

    Ground truth analysis (550 schools, 11 countries) showed:
      score >= 95: median 0.2km, 87% < 5km → genuine street match
      score 90-95: median 4.4km, 51% < 5km → likely locality/centroid
      score < 90:  median 8.1km, 40% < 5km → municipal centroid at best

    See results/geocoder_ground_truth_score_analysis.csv for evidence.
    """
    if score is not None and score >= 95:
        return "street"
    if score is not None and score >= 90:
        return "centroid"
    # score < 90: always uncertain, regardless of query level
    if score is not None:
        return "uncertain"
    # No score (non-ArcGIS geocoder): classify by query type
    if query_precision in ("admin",):
        return "centroid"
    return "uncertain"


def geocode_school(queries, geocoders, cache, bbox=None):
    """Try geocoding with query cascade × geocoder cascade.
    Returns (lat, lon, source, precision, query, score) or Nones.
    bbox: (lat_min, lat_max, lon_min, lon_max) — reject results outside this box.

    Precision is reclassified by ArcGIS score:
      score >= 95 → "street"   (accept for fill + compare diagnostic)
      score 90-95 → "centroid" (accept for fill only)
      score < 90  → "uncertain" (reject)
    """
    for query, precision in queries:
        query_clean = query.strip(", ")

        # Check cache
        if query_clean in cache:
            cached = cache[query_clean]
            if cached is not None:
                cached_score = cached.get("score")
                real_precision = _score_to_precision(cached_score, precision)
                return cached["lat"], cached["lon"], cached.get("source", "cache"), real_precision, query_clean, cached_score
            continue  # cached failure

        # Try each geocoder for this query before moving to next query level
        for source_name, geocoder_fn in geocoders:
            try:
                location = geocoder_fn(query_clean)
                if location:
                    lat, lon = location.latitude, location.longitude
                    # Bbox validation: reject results outside the country
                    if bbox:
                        lat_min, lat_max, lon_min, lon_max = bbox
                        margin = 1  # degree margin for islands/borders
                        if lat < lat_min - margin or lat > lat_max + margin or \
                           lon < lon_min - margin or lon > lon_max + margin:
                            continue  # result outside country, try next geocoder
                    # Capture ArcGIS score (other geocoders return None)
                    score = None
                    if hasattr(location, "raw") and isinstance(location.raw, dict):
                        score = location.raw.get("score")
                    real_precision = _score_to_precision(score, precision)
                    cache[query_clean] = {
                        "lat": lat, "lon": lon,
                        "display": location.address,
                        "source": source_name,
                        "score": score,
                    }
                    return lat, lon, source_name, real_precision, query_clean, score
            except Exception:
                continue  # try next geocoder for same query
        # All geocoders failed for this query — cache failure, try next query level
        cache[query_clean] = None

    return None, None, None, None, None, None


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def process_country(iso, cfg, extract_addresses_fn, geocoders, cache,
                    dry_run=False, skip_dup_coords=False, retry_centroids=False):
    """Geocode all target schools for one country."""

    # Load addresses first (needed for centroid detection fuzzy filter)
    addr_df = extract_addresses_fn(iso, cfg) if cfg else None

    cima, missing, zeros, mismatches, dup_addr, coord_centroids = identify_targets(iso, addr_df)
    if cima.empty:
        return None

    # Combine targets
    fill_targets = missing | zeros  # these get latitud/longitud filled directly
    compare_targets = mismatches  # these get _geocoded columns
    if not skip_dup_coords:
        compare_targets = compare_targets | dup_addr
    # Always include detected centroids (original + geocoded) for re-geocoding
    compare_targets = compare_targets | coord_centroids

    all_targets = fill_targets | compare_targets
    if not all_targets:
        print(f"  {iso}: no schools to geocode")
        return None

    n_centroids = len(coord_centroids - missing - zeros - mismatches - dup_addr)
    print(f"  {iso}: {len(all_targets):,} targets "
          f"(fill={len(fill_targets):,}, compare={len(compare_targets):,}, "
          f"centroids_new={n_centroids:,})")

    # Retry centroids: clear cached queries for centroid schools so geocoders retry
    if retry_centroids and coord_centroids:
        cleared = 0
        for key, val in list(cache.items()):
            if val and val.get("source") == "arcgis":
                # Check if this cached result is a centroid point
                lat_r = round(val["lat"], 3)
                lon_r = round(val["lon"], 3)
                geo_key = f"{lat_r},{lon_r}"
                # Count how many cache entries map to same point
                # Simple heuristic: just clear all arcgis entries for this country's queries
                if cfg and cfg["country_name"].lower() in key.lower():
                    del cache[key]
                    cleared += 1
        if cleared:
            print(f"    Cleared {cleared} ArcGIS cache entries for centroid retry")

    if dry_run:
        return {"iso": iso, "fill": len(fill_targets), "compare": len(compare_targets),
                "centroids_new": n_centroids, "total": len(all_targets)}

    if addr_df is None or addr_df.empty:
        print(f"    No address data available")
        return None

    country_name = cfg["country_name"]

    # Merge addresses with target schools
    target_df = cima[cima["id_centro"].isin(all_targets)].copy()
    target_df = target_df.merge(addr_df, on="id_centro", how="left", suffixes=("", "_addr"))

    results = []
    n_success = 0
    n_fail = 0
    t0 = time.time()

    for i, (_, row) in enumerate(target_df.iterrows()):
        queries = build_queries(row, country_name)
        if not queries:
            n_fail += 1
            results.append({
                "iso": iso,
                "id_centro": row["id_centro"],
                "geocoded_lat": np.nan,
                "geocoded_lon": np.nan,
                "geocode_source": None,
                "geocode_precision": "no_address",
                "geocode_query": "",
                "target_type": "fill" if row["id_centro"] in fill_targets else "compare",
            })
            continue

        bbox = COUNTRY_BBOX.get(iso)
        lat, lon, source, precision, query, score = geocode_school(queries, geocoders, cache, bbox=bbox)

        if lat is not None:
            n_success += 1
        else:
            n_fail += 1

        # Distance from original coords (for compare targets)
        dist_km = np.nan
        orig_lat = row.get("latitud")
        orig_lon = row.get("longitud")
        if lat is not None and pd.notna(orig_lat) and pd.notna(orig_lon) and orig_lat != 0:
            dist_km = haversine_km(orig_lat, orig_lon, lat, lon)

        results.append({
            "iso": iso,
            "id_centro": row["id_centro"],
            "nombre_centro": row.get("nombre_centro", ""),
            "geocoded_lat": lat,
            "geocoded_lon": lon,
            "geocode_source": source,
            "geocode_precision": precision or "failed",
            "arcgis_score": score,
            "geocode_query": query or "",
            "geocode_distance_km": dist_km,
            "target_type": "fill" if row["id_centro"] in fill_targets else "compare",
            "original_lat": orig_lat if pd.notna(orig_lat) else np.nan,
            "original_lon": orig_lon if pd.notna(orig_lon) else np.nan,
        })

        # Progress + periodic cache save
        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            remaining = (len(target_df) - i - 1) / rate if rate > 0 else 0
            print(f"    {i+1:,}/{len(target_df):,} ({n_success} ok, {n_fail} fail) "
                  f"[{rate:.1f}/s, ~{remaining/60:.0f}min left]")
        if (i + 1) % 500 == 0:
            # Save cache periodically to avoid losing progress on crash
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)
            print(f"    [cache saved: {len(cache):,} entries]")

    elapsed = time.time() - t0
    print(f"    Done: {n_success:,} geocoded, {n_fail:,} failed ({elapsed:.0f}s)")

    results_df = pd.DataFrame(results)

    # --- Centroid detection on geocoded results ---
    all_geocoded = results_df[results_df["geocoded_lat"].notna()].copy()
    if not all_geocoded.empty:
        all_geocoded["geo_key"] = (
            all_geocoded["geocoded_lat"].round(3).astype(str) + "," +
            all_geocoded["geocoded_lon"].round(3).astype(str)
        )
        point_counts = all_geocoded["geo_key"].value_counts()
        centroid_points = set(point_counts[point_counts >= 5].index)
        if centroid_points:
            centroid_ids = set(all_geocoded[all_geocoded["geo_key"].isin(centroid_points)]["id_centro"])
            # Only downgrade "street" → "centroid". Do NOT promote "uncertain" → "centroid".
            # Score-based classification takes priority over cluster detection.
            downgrade_mask = (
                results_df["id_centro"].isin(centroid_ids) &
                results_df["geocoded_lat"].notna() &
                (results_df["geocode_precision"] == "street")
            )
            n_downgraded = downgrade_mask.sum()
            results_df.loc[downgrade_mask, "geocode_precision"] = "centroid"
            print(f"    Centroids detected: {len(centroid_ids):,} schools at {len(centroid_points)} shared points "
                  f"({n_downgraded} downgraded street→centroid)")

    # --- Spatial validation + acceptance criteria ---
    print("    Validating geocoded coords against admin boundaries...")
    results_df = validate_geocoded(results_df, addr_df, iso)

    accept_counts = results_df[results_df["acceptance"] != ""]["acceptance"].value_counts()
    for level, count in accept_counts.items():
        print(f"    {level}: {count:,}")

    # --- Update CIMA file ---
    # Initialize columns
    for col in ["latitud_geocoded", "longitud_geocoded", "geocode_distance_km", "arcgis_score"]:
        if col not in cima.columns:
            cima[col] = np.nan
    for col in ["geocode_source", "geocode_precision", "acceptance",
                 "coordinate_source", "coordinate_quality"]:
        if col not in cima.columns:
            cima[col] = ""

    # Default: all schools with existing valid coords → source=original, quality=gps
    has_coords = cima["latitud"].notna() & (cima["latitud"] != 0) & (cima["longitud"] != 0)
    cima.loc[has_coords & (cima["coordinate_quality"] == ""), "coordinate_quality"] = "gps"
    cima.loc[has_coords & (cima["coordinate_source"] == ""), "coordinate_source"] = "original"

    # --- FILL targets: write geocoded coords where accepted ---
    fill_write = ["ACCEPT", "ACCEPT_WITH_FLAG", "ACCEPT_CENTROID"]
    fill_accepted = results_df[
        (results_df["target_type"] == "fill") &
        results_df["geocoded_lat"].notna() &
        results_df["acceptance"].isin(fill_write)
    ]
    if not fill_accepted.empty:
        fill_map = fill_accepted.set_index("id_centro")
        for sid in fill_map.index:
            mask = cima["id_centro"] == sid
            if mask.any():
                idx = cima.index[mask][0]
                prec = fill_map.loc[sid, "geocode_precision"]
                cima.loc[idx, "latitud"] = fill_map.loc[sid, "geocoded_lat"]
                cima.loc[idx, "longitud"] = fill_map.loc[sid, "geocoded_lon"]
                cima.loc[idx, "geocode_source"] = fill_map.loc[sid, "geocode_source"]
                cima.loc[idx, "geocode_precision"] = prec
                cima.loc[idx, "arcgis_score"] = fill_map.loc[sid, "arcgis_score"]
                cima.loc[idx, "acceptance"] = fill_map.loc[sid, "acceptance"]
                cima.loc[idx, "coordinate_source"] = "geocoded"
                cima.loc[idx, "coordinate_quality"] = "street" if prec == "street" else "centroid"

    fill_rejected = results_df[
        (results_df["target_type"] == "fill") &
        (~results_df["acceptance"].isin(fill_write))
    ]
    n_fill_ok = len(fill_accepted)
    n_fill_rej = len(fill_rejected)
    if n_fill_ok + n_fill_rej > 0:
        print(f"    Fill: {n_fill_ok:,} accepted, {n_fill_rej:,} rejected (left as NaN)")

    # --- COMPARE targets: NEVER replace GPS. Write QC audit columns only. ---
    compare_all = results_df[
        (results_df["target_type"] == "compare") &
        results_df["geocoded_lat"].notna()
    ]
    if not compare_all.empty:
        comp_map = compare_all.set_index("id_centro")
        n_keep = 0
        n_flag = 0
        for sid in comp_map.index:
            mask = cima["id_centro"] == sid
            if not mask.any():
                continue
            idx = cima.index[mask][0]
            acc = comp_map.loc[sid, "acceptance"]

            # Write QC audit columns (geocoded alternative for reference)
            cima.loc[idx, "latitud_geocoded"] = comp_map.loc[sid, "geocoded_lat"]
            cima.loc[idx, "longitud_geocoded"] = comp_map.loc[sid, "geocoded_lon"]
            cima.loc[idx, "geocode_source"] = comp_map.loc[sid, "geocode_source"]
            cima.loc[idx, "geocode_precision"] = comp_map.loc[sid, "geocode_precision"]
            cima.loc[idx, "geocode_distance_km"] = comp_map.loc[sid, "geocode_distance_km"]
            cima.loc[idx, "arcgis_score"] = comp_map.loc[sid, "arcgis_score"]
            cima.loc[idx, "acceptance"] = acc

            # GPS always preserved. Flag discrepancy in coordinate_quality.
            cima.loc[idx, "coordinate_source"] = "original"
            if acc == "KEEP_ORIGINAL":
                # GPS confirmed in declared municipality — no flag needed
                n_keep += 1
            else:
                # FLAG: address doesn't match GPS location — QC discrepancy
                cima.loc[idx, "coordinate_quality"] = "flag"
                n_flag += 1

        print(f"    Compare: {n_keep:,} confirmed, {n_flag:,} flagged (GPS kept, address discrepancy)")

    # Save updated CIMA
    cima_path = BASE / iso / "processed" / f"{iso}_total_cima.csv"
    cima.to_csv(cima_path, index=False, encoding="utf-8")

    return results_df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Phase B-1: Geocode schools")
    parser.add_argument("--countries", nargs="+", help="ISO codes to process (default: all Phase B-1)")
    parser.add_argument("--dry-run", action="store_true", help="Preview targets without geocoding")
    parser.add_argument("--skip-dup-coords", action="store_true", help="Skip duplicate-coord schools")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cache, re-geocode everything")
    parser.add_argument("--retry-centroids", action="store_true",
                        help="Clear ArcGIS cache for centroid points and retry with other geocoders")
    args = parser.parse_args()

    isos = args.countries or PHASE_B1_ISOS

    # Load config
    print("Loading address configurations...")
    country_config, extract_addresses_fn = load_country_config()

    # Load cache
    cache = {}
    if not args.no_cache and CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    print(f"  Cache: {len(cache):,} entries")

    # Setup geocoders
    geocoders = []
    if not args.dry_run:
        print("Initializing geocoders...")
        geocoders = setup_geocoders()
        print(f"  Active: {[g[0] for g in geocoders]}")

    # Process countries
    print()
    print("=" * 60)
    print("  Phase B-1: Geocoding")
    print("=" * 60)

    all_results = []
    for iso in isos:
        cfg = country_config.get(iso)
        if cfg is None or cfg.get("skip"):
            print(f"  {iso}: not in COUNTRY_CONFIG — skipped")
            continue

        result = process_country(iso, cfg, extract_addresses_fn, geocoders, cache,
                                 dry_run=args.dry_run, skip_dup_coords=args.skip_dup_coords,
                                 retry_centroids=args.retry_centroids)
        if result is not None:
            if isinstance(result, dict):
                # dry run
                all_results.append(result)
            else:
                all_results.append(result)

    # Save cache
    if not args.dry_run and cache:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        print(f"\nCache saved: {len(cache):,} entries → {CACHE_PATH}")

    # Save results
    if not args.dry_run and all_results:
        combined = pd.concat([r for r in all_results if isinstance(r, pd.DataFrame)], ignore_index=True)
        combined.to_csv(RESULTS / "geocode_results.csv", index=False, encoding="utf-8")
        print(f"Results saved: {len(combined):,} rows → results/geocode_results.csv")

        # Comparison file for mismatch/dup schools
        comparison = combined[combined["target_type"] == "compare"].copy()
        if not comparison.empty:
            comparison.to_csv(RESULTS / "geocode_comparison.csv", index=False, encoding="utf-8")
            print(f"Comparison saved: {len(comparison):,} rows → results/geocode_comparison.csv")

    # Dry run summary
    if args.dry_run and all_results:
        print("\n--- DRY RUN SUMMARY ---")
        total_fill = sum(r["fill"] for r in all_results)
        total_compare = sum(r["compare"] for r in all_results)
        total_centroids = sum(r.get("centroids_new", 0) for r in all_results)
        print(f"{'ISO':<5} {'Fill':>8} {'Compare':>8} {'Centr':>7} {'Total':>8}")
        print("-" * 42)
        for r in all_results:
            print(f"{r['iso']:<5} {r['fill']:>8,} {r['compare']:>8,} {r.get('centroids_new',0):>7,} {r['total']:>8,}")
        print("-" * 42)
        total_all = total_fill + total_compare
        print(f"TOTAL {total_fill:>8,} {total_compare:>8,} {total_centroids:>7,} {total_all:>8,}")
        est_sec = total_all / 2  # ~2 schools/s effective rate
        print(f"\nEstimated time at ~2 req/s: {est_sec/3600:.1f} hours")


if __name__ == "__main__":
    main()
