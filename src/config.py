"""Shared paths and constants for the Dubai real estate pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "clean"
MARTS_DIR = ROOT / "data" / "marts"
REFERENCE_DIR = ROOT / "data" / "reference"   # small hand-collected lookups (committed)
SQL_DIR = ROOT / "sql"
DB_PATH = ROOT / "data" / "dubai_real_estate.duckdb"
DASHBOARD_DIR = ROOT / "dashboard"
POWERBI_DIR = ROOT / "powerbi"

SQM_TO_SQFT = 10.7639

# Sanity limits used to drop data-entry errors (AED per sq ft).
MIN_PRICE_SQFT = 100
MAX_PRICE_SQFT = 20_000
MIN_SIZE_SQM = 10

for d in (CLEAN_DIR, MARTS_DIR):
    d.mkdir(parents=True, exist_ok=True)
