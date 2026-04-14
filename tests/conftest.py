"""Shared fixtures for CIMA pipeline tests."""

import pandas as pd
import pytest
from pathlib import Path

CIMA_DIR = Path("data/schools/AR")
RESULTS_DIR = Path("results")

REQUIRED_COLUMNS = [
    "id_centro", "nombre_centro", "sector",
    "nivel_primaria", "nivel_secbaja", "nivel_secalta",
    "latitud", "longitud", "adm0_pcode",
]

# Active ISOs (BHS and HTI excluded from analysis)
ALL_ISOS = [
    "ARG", "BLZ", "BOL", "BRA", "BRB", "CHL", "COL", "CRI",
    "DOM", "ECU", "GTM", "GUY", "HND", "JAM", "MEX", "PAN",
    "PER", "PRY", "SLV", "SUR", "URY",
]

# Approximate lat/lon bounding box per country (min_lat, max_lat, min_lon, max_lon)
COUNTRY_BBOX = {
    "ARG": (-56, -21, -74, -53),
    "BHS": ( 20,  28, -80, -72),
    "BLZ": ( 15,  19, -90, -87),
    "BOL": (-23, -9,  -70, -57),
    "BRA": (-34,  6,  -74, -32),
    "BRB": ( 13,  14, -60, -59),
    "CHL": (-56, -17, -76, -66),
    "COL": (-5,   14, -82, -66),
    "CRI": (  8,  12, -86, -82),
    "DOM": ( 17,  20, -72, -68),
    "ECU": (-5,    2, -81, -75),
    "GTM": ( 13,  18, -93, -88),
    "GUY": (  1,   9, -62, -56),
    "HND": ( 13,  17, -90, -83),
    "HTI": ( 18,  20, -75, -71),
    "JAM": ( 17,  19, -79, -76),
    "MEX": ( 14,  33,-118, -86),
    "PAN": (  7,  10, -83, -77),
    "PER": (-19,   0, -82, -68),
    "PRY": (-28, -19, -63, -54),
    "SLV": ( 13,  15, -91, -87),
    "SUR": (  1,   6, -59, -53),
    "URY": (-35, -30, -59, -53),
}


def _cima_path(iso):
    return CIMA_DIR / iso / "processed" / f"{iso}_total_cima.csv"


@pytest.fixture(scope="session")
def all_cima():
    """Load all CIMA files into a dict {iso: DataFrame}."""
    data = {}
    for iso in ALL_ISOS:
        path = _cima_path(iso)
        if path.exists():
            data[iso] = pd.read_csv(path, dtype={"id_centro": str})
    return data


def pytest_generate_tests(metafunc):
    """Parametrize tests that use 'iso' fixture by all available CIMA files."""
    if "iso" in metafunc.fixturenames:
        available = [iso for iso in ALL_ISOS if _cima_path(iso).exists()]
        metafunc.parametrize("iso", available)
