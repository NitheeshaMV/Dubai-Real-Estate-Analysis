"""Step 1 - load the raw DLD CSV exports, clean them and save one tidy sales table.

Input : data/raw/*.csv  (DLD Open Data -> Transactions -> Sales -> Download as CSV)
Output: data/clean/sales_clean.parquet + a `sales` table in data/dubai_real_estate.duckdb
"""
import re

import duckdb
import pandas as pd

from config import (CLEAN_DIR, DB_PATH, MAX_PRICE_SQFT, MIN_PRICE_SQFT,
                    MIN_SIZE_SQM, RAW_DIR, REFERENCE_DIR, SQM_TO_SQFT)

# DLD column -> our column. The export uses these names (English fields end in _EN).
COLUMNS = {
    "TRANSACTION_NUMBER": "transaction_id",
    "INSTANCE_DATE": "transaction_date",
    "GROUP_EN": "transaction_group",
    "PROCEDURE_EN": "procedure",
    "IS_OFFPLAN_EN": "registration_type",
    "IS_FREE_HOLD_EN": "freehold",
    "USAGE_EN": "usage",
    "AREA_EN": "area",
    "PROP_TYPE_EN": "property_type",
    "PROP_SB_TYPE_EN": "property_sub_type",
    "TRANS_VALUE": "price_aed",
    "PROCEDURE_AREA": "size_sqm",
    "ACTUAL_AREA": "actual_size_sqm",
    "ROOMS_EN": "rooms",
    "PARKING": "parking",
    "NEAREST_METRO_EN": "nearest_metro",
    "NEAREST_MALL_EN": "nearest_mall",
    "NEAREST_LANDMARK_EN": "nearest_landmark",
    "PROJECT_EN": "project",
}
# Dropped on purpose: TOTAL_BUYER / TOTAL_SELLER are always 0 in the open export and
# MASTER_PROJECT_EN is empty for >99% of rows.

# (property type, sub type) -> the segment buyers actually think in.
SEGMENTS = {
    ("Unit", "Flat"): "Apartment",
    ("Unit", "Hotel Apartment"): "Hotel",
    ("Unit", "Hotel Rooms"): "Hotel",
    ("Unit", "Office"): "Commercial",
    ("Unit", "Shop"): "Commercial",
    ("Building", "Villa"): "Villa",
}
RESIDENTIAL_SEGMENTS = {"Apartment", "Villa"}


def normalise_header(name: str) -> str:
    """Map whatever header the export uses (code or label) to the DLD code."""
    key = re.sub(r"[^A-Z0-9]+", "_", str(name).strip().upper()).strip("_")
    labels = {  # on-screen labels, in case the export ships those instead
        "TRANSACTION_DATE": "INSTANCE_DATE", "TRANSACTION_TYPE": "GROUP_EN",
        "TRANSACTION_SUB_TYPE": "PROCEDURE_EN", "REGISTRATION_TYPE": "IS_OFFPLAN_EN",
        "IS_FREE_HOLD": "IS_FREE_HOLD_EN", "USAGE": "USAGE_EN", "AREA": "AREA_EN",
        "PROPERTY_TYPE": "PROP_TYPE_EN", "PROPERTY_SUB_TYPE": "PROP_SB_TYPE_EN",
        "AMOUNT": "TRANS_VALUE", "TRANSACTION_SIZE_SQ_M": "PROCEDURE_AREA",
        "PROPERTY_SIZE_SQ_M": "ACTUAL_AREA", "ROOM_S": "ROOMS_EN",
        "NEAREST_METRO": "NEAREST_METRO_EN", "NEAREST_MALL": "NEAREST_MALL_EN",
        "NEAREST_LANDMARK": "NEAREST_LANDMARK_EN", "NO_OF_BUYER": "TOTAL_BUYER",
        "NO_OF_SELLER": "TOTAL_SELLER", "MASTER_PROJECT": "MASTER_PROJECT_EN",
        "PROJECT": "PROJECT_EN",
    }
    return labels.get(key, key)


KEEP_UPPER = {"MBR", "TECOM", "DMCC-EZ2", "I", "II", "III"}


def tidy_name(name):
    """Title-case ALL-CAPS names (keeping codes like MBR, TECOM); leave mixed-case names alone."""
    if not isinstance(name, str) or not name.isupper():
        return name
    return " ".join(w if w in KEEP_UPPER else w.capitalize() for w in name.split())


def load_raw() -> pd.DataFrame:
    files = [f for f in sorted(RAW_DIR.glob("*.csv")) if "rent" not in f.name.lower()]
    if not files:
        raise SystemExit(f"No sales CSV found in {RAW_DIR}")
    frames = []
    for f in files:
        df = pd.read_csv(f, dtype=str, encoding="utf-8-sig")
        df.columns = [normalise_header(c) for c in df.columns]
        frames.append(df)
        print(f"loaded {f.name}: {len(df):,} rows")
    return pd.concat(frames, ignore_index=True)


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = raw[[c for c in COLUMNS if c in raw.columns]].rename(columns=COLUMNS)
    log = {"raw_rows": len(df)}

    # The export repeats a sale once per nearby metro station -> keep one row per transaction.
    df = df.drop_duplicates(subset="transaction_id")
    log["after_dedupe"] = len(df)

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce", format="ISO8601")
    for col in ("price_aed", "size_sqm", "actual_size_sqm"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in df.select_dtypes("object"):
        df[col] = df[col].str.strip().replace({"": pd.NA, "null": pd.NA, "None": pd.NA})

    # DLD mixes "JUMEIRAH VILLAGE CIRCLE" and "Al Yelayiss 1" -> one consistent casing.
    df["area"] = df["area"].map(tidy_name)

    df = df[df["transaction_group"].eq("Sales")]
    df = df.dropna(subset=["transaction_date", "price_aed", "size_sqm"])
    df = df[(df["price_aed"] > 0) & (df["size_sqm"] >= MIN_SIZE_SQM)]
    log["valid_price_and_size"] = len(df)

    df["price_per_sqft"] = df["price_aed"] / (df["size_sqm"] * SQM_TO_SQFT)
    df["size_sqft"] = df["size_sqm"] * SQM_TO_SQFT
    df["segment"] = [
        SEGMENTS.get((t, s), "Land" if t == "Land" else "Other")
        for t, s in zip(df["property_type"], df["property_sub_type"])
    ]
    # Price-per-sq-ft sanity check only where it is meaningful (homes); land is often
    # sold far below 100 AED/sq ft on the city edge, so it is kept as is.
    is_home = df["segment"].isin(RESIDENTIAL_SEGMENTS)
    insane = is_home & ~df["price_per_sqft"].between(MIN_PRICE_SQFT, MAX_PRICE_SQFT)
    log["dropped_price_outliers"] = int(insane.sum())
    df = df[~insane]

    df["month"] = df["transaction_date"].dt.to_period("M").dt.to_timestamp()
    df["is_offplan"] = df["registration_type"].eq("Off-Plan")
    df["is_residential"] = df["segment"].isin(RESIDENTIAL_SEGMENTS)
    df["rooms"] = df["rooms"].fillna("Unknown")
    df["price_band"] = pd.cut(
        df["price_aed"],
        bins=[0, 1e6, 2e6, 5e6, 10e6, float("inf")],
        labels=["Under 1M", "1-2M", "2-5M", "5-10M", "10M+"],
    ).astype(str)
    log["clean_rows"] = len(df)
    return df.reset_index(drop=True), log


RENT_COLUMNS = {
    "REGISTRATION_DATE": "registration_date",
    "VERSION_EN": "contract_type",
    "AREA_EN": "area",
    "ANNUAL_AMOUNT": "annual_rent_aed",
    "ACTUAL_AREA": "size_sqm",
    "PROP_TYPE_EN": "property_type",
    "PROP_SUB_TYPE_EN": "property_sub_type",
    "ROOMS": "rooms",
    "USAGE_EN": "usage",
    "TOTAL_PROPERTIES": "properties_in_contract",
    "PROJECT_EN": "project",
}


def clean_rents() -> pd.DataFrame | None:
    """Rents (Ejari) export -> one row per single-property residential lease."""
    files = sorted(RAW_DIR.glob("*rent*.csv"))
    if not files:
        return None
    raw = pd.concat([pd.read_csv(f, dtype=str, encoding="utf-8-sig") for f in files], ignore_index=True)
    print(f"loaded {len(files)} rent file(s): {len(raw):,} rows")
    # Same duplication as sales (one row per nearby metro): drop it before trimming columns.
    raw = raw.drop_duplicates(subset=[c for c in raw.columns if not c.startswith("NEAREST_")])
    # Some contracts are also repeated once per sub-project of a master community (e.g. one Creek Beach
    # lease listed under all 12 Creek Beach buildings). The real building is unknown, so drop them all.
    same_but_project = [c for c in raw.columns if c != "PROJECT_EN" and not c.startswith("NEAREST_")]
    ambiguous = raw.duplicated(subset=same_but_project, keep=False)
    print(f"leases listed under several buildings (dropped): {int(ambiguous.sum()):,} rows")
    raw = raw[~ambiguous]
    df = raw[[c for c in RENT_COLUMNS if c in raw.columns]].rename(columns=RENT_COLUMNS)
    for col in df.select_dtypes("object"):
        df[col] = df[col].str.strip()                  # e.g. "Studio " has a trailing space
    df["registration_date"] = pd.to_datetime(df["registration_date"], errors="coerce", format="ISO8601")
    for col in ("annual_rent_aed", "size_sqm", "properties_in_contract"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["area"] = df["area"].map(tidy_name)
    # Labour camps, staff accommodation etc. are not homes an investor would compare with sales.
    df["segment"] = df["property_sub_type"].map({"Flat": "Apartment", "Studio": "Apartment", "Villa": "Villa"})
    df = df[df["usage"].eq("Residential") & df["segment"].notna() & df["properties_in_contract"].eq(1)]
    df = df[(df["size_sqm"] >= MIN_SIZE_SQM) & df["annual_rent_aed"].between(10_000, 5_000_000)]
    df["rent_per_sqft"] = df["annual_rent_aed"] / (df["size_sqm"] * SQM_TO_SQFT)
    df = df[df["rent_per_sqft"].between(10, 1_000)]
    print(f"clean single-unit residential leases: {len(df):,}")
    return df.reset_index(drop=True)


def load_service_charges(con) -> None:
    """RERA-approved service charges (DLD Service Charge Index) for each yield area's most-leased building.

    DLD only shows these one project at a time behind a captcha, so they were looked up by hand into
    data/reference/service_charges_2026.csv. Without the file the table is empty and only gross yield is shown.
    """
    path = REFERENCE_DIR / "service_charges_2026.csv"
    if path.exists():
        con.execute("CREATE OR REPLACE TABLE service_charges AS SELECT * FROM read_csv(?, header = true)", [str(path)])
    else:
        con.execute("CREATE OR REPLACE TABLE service_charges (area VARCHAR, dld_project VARCHAR, "
                    "budget_year INTEGER, service_charge_aed_sqft DOUBLE)")
    print(f"service charges: {con.execute('SELECT COUNT(*) FROM service_charges').fetchone()[0]} areas")


def main() -> None:
    df, log = clean(load_raw())
    out = CLEAN_DIR / "sales_clean.parquet"
    df.to_parquet(out, index=False)
    rents = clean_rents()
    with duckdb.connect(str(DB_PATH)) as con:
        con.execute("CREATE OR REPLACE TABLE sales AS SELECT * FROM read_parquet(?)", [str(out)])
        if rents is not None:
            rents.to_parquet(CLEAN_DIR / "rents_clean.parquet", index=False)
            con.register("rents_df", rents)
            con.execute("CREATE OR REPLACE TABLE rents AS SELECT * FROM rents_df")
            log["rent_rows"] = len(rents)
        load_service_charges(con)
    pd.Series(log).to_csv(CLEAN_DIR / "cleaning_log.csv", header=["rows"])
    for k, v in log.items():
        print(f"{k:>24}: {v:,}")
    print(f"saved {out} and table `sales` in {DB_PATH.name}")


if __name__ == "__main__":
    main()
