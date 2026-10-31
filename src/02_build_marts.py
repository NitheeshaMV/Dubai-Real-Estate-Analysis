"""Step 2 - run every query in sql/ against DuckDB and save each result as a CSV mart.

The marts feed the dashboard, the notebook and the Power BI model.
"""
import duckdb

from config import DB_PATH, MARTS_DIR, SQL_DIR


def main() -> None:
    with duckdb.connect(str(DB_PATH)) as con:
        for sql_file in sorted(SQL_DIR.glob("*.sql")):
            name = sql_file.stem.split("_", 1)[1]          # 01_monthly_market -> monthly_market
            try:
                df = con.execute(sql_file.read_text(encoding="utf-8")).df()
            except duckdb.CatalogException as e:           # e.g. no rents exported yet
                print(f"{sql_file.name:<28} -> skipped ({str(e).splitlines()[0]})")
                continue
            con.execute(f"CREATE OR REPLACE TABLE mart_{name} AS SELECT * FROM df")
            df.to_csv(MARTS_DIR / f"{name}.csv", index=False)
            print(f"{sql_file.name:<28} -> marts/{name}.csv ({len(df):,} rows)")


if __name__ == "__main__":
    main()
