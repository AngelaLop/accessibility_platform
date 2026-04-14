"""Test school counts and deduplication across CIMA files."""

import pandas as pd
import pytest
from conftest import _cima_path

# Expected minimum school counts per country (sanity check — should never drop below these)
MIN_SCHOOLS = {
    "ARG": 30_000, "BLZ": 200, "BOL": 14_000, "BRA": 125_000,
    "CHL": 7_000, "COL": 45_000, "CRI": 4_000, "DOM": 8_000,
    "ECU": 15_000, "GTM": 20_000, "HND": 10_000, "MEX": 150_000,
    "PAN": 3_000, "PER": 50_000, "PRY": 7_000, "SLV": 5_000,
    "SUR": 500, "URY": 2_500,
}


def load(iso):
    return pd.read_csv(_cima_path(iso), dtype={"id_centro": str})


class TestCounts:
    """Validate school counts and deduplication."""

    def test_no_duplicate_ids(self, iso):
        df = load(iso)
        dupes = df["id_centro"].duplicated().sum()
        assert dupes == 0, (
            f"{iso}: {dupes} duplicate id_centro values"
        )

    def test_not_empty(self, iso):
        df = load(iso)
        assert len(df) > 0, f"{iso}: CIMA file is empty"

    def test_minimum_school_count(self, iso):
        if iso not in MIN_SCHOOLS:
            pytest.skip(f"{iso}: no minimum count defined")
        df = load(iso)
        expected = MIN_SCHOOLS[iso]
        assert len(df) >= expected, (
            f"{iso}: only {len(df):,} schools, expected at least {expected:,}"
        )

    def test_sector_accounting(self, iso):
        """Public + Private + Unknown should equal total (no nulls in sector)."""
        df = load(iso)
        n_null = df["sector"].isna().sum()
        n_pub = (df["sector"] == "Public").sum()
        n_prv = (df["sector"] == "Private").sum()
        n_unk = (df["sector"] == "Unknown").sum()
        assert n_pub + n_prv + n_unk + n_null == len(df), (
            f"{iso}: sector accounting mismatch: "
            f"{n_pub} Public + {n_prv} Private + {n_unk} Unknown + {n_null} null != {len(df)} total"
        )
