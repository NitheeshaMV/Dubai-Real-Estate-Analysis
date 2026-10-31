"""Step 5 - export a star schema for Power BI (powerbi/model/*.csv).

fact_sales  - one row per sale, with keys to the dimensions
dim_date    - calendar table (mark it as the date table in Power BI)
dim_area    - one row per area, with its nearest metro and mall
dim_property- property segment / sub-type / bedrooms combinations
fact_rent_yield - area-level rental yield (only when rents were exported)
fact_price_index- monthly like-for-like vs simple-average apartment price index
"""
import duckdb

from config import DB_PATH, POWERBI_DIR

OUT = POWERBI_DIR / "model"
OUT.mkdir(parents=True, exist_ok=True)

QUERIES = {
    "dim_date": """
        SELECT CAST(d AS DATE) AS date,
               year(d) AS year, quarter(d) AS quarter, month(d) AS month_number,
               strftime(d, '%b') AS month_name, strftime(d, '%Y-%m') AS year_month,
               weekofyear(d) AS week, dayname(d) AS weekday
        FROM range(DATE_TRUNC('month', (SELECT MIN(transaction_date) FROM sales)),
                   (SELECT MAX(transaction_date) FROM sales) + INTERVAL 1 DAY, INTERVAL 1 DAY) t(d)
    """,
    "dim_area": """
        SELECT DENSE_RANK() OVER (ORDER BY area) AS area_key, area,
               MODE(nearest_metro) AS nearest_metro, MODE(nearest_mall) AS nearest_mall,
               MODE(nearest_landmark) AS nearest_landmark
        FROM sales WHERE area IS NOT NULL GROUP BY area
    """,
    "dim_property": """
        SELECT DENSE_RANK() OVER (ORDER BY segment, property_sub_type, rooms) AS property_key,
               segment, property_type, property_sub_type, rooms
        FROM (SELECT DISTINCT segment, property_type, property_sub_type, rooms FROM sales)
    """,
    "fact_sales": """
        SELECT s.transaction_id, CAST(s.transaction_date AS DATE) AS date,
               a.area_key, p.property_key, s.project, s.procedure,
               s.is_offplan, CASE WHEN s.is_offplan THEN 'Off-plan' ELSE 'Ready' END AS registration,
               s.freehold = 'Free Hold' AS is_freehold,
               s.price_aed, ROUND(s.size_sqft, 1) AS size_sqft,
               ROUND(s.price_per_sqft, 1) AS price_per_sqft, s.price_band,
               CASE s.price_band WHEN 'Under 1M' THEN 1 WHEN '1-2M' THEN 2 WHEN '2-5M' THEN 3
                                 WHEN '5-10M' THEN 4 ELSE 5 END AS price_band_order
        FROM sales s
        JOIN dim_area a USING (area)
        JOIN dim_property p ON p.segment = s.segment AND p.rooms = s.rooms
             AND p.property_type = s.property_type
             AND p.property_sub_type IS NOT DISTINCT FROM s.property_sub_type
    """,
}


def main() -> None:
    with duckdb.connect(str(DB_PATH)) as con:
        for name, sql in QUERIES.items():
            con.execute(f"CREATE OR REPLACE TEMP TABLE {name} AS {sql}")
            path = OUT / f"{name}.csv"
            con.execute(f"COPY {name} TO '{path.as_posix()}' (HEADER, DELIMITER ',')")
            print(f"{name:<14} {con.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]:>8,} rows -> {path.name}")
        # Area- and month-level marts that Power BI uses as small fact tables
        for mart, name in (("mart_rental_yield", "fact_rent_yield"), ("mart_price_index", "fact_price_index")):
            if con.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{mart}'").fetchone()[0]:
                path = OUT / f"{name}.csv"
                # month is a timestamp in DuckDB; Power BI's date type needs a plain date
                select = {
                    "fact_price_index": "SELECT * REPLACE (CAST(month AS DATE) AS month)",
                    # AED millions / thousands read the same in every regional digit grouping
                    "fact_rent_yield": "SELECT *, ROUND(median_price_aed / 1e6, 2) AS median_price_aed_m, "
                                       "ROUND(median_annual_rent_aed / 1e3, 1) AS median_annual_rent_aed_k",
                }.get(name, "SELECT *")
                con.execute(f"COPY ({select} FROM {mart}) TO '{path.as_posix()}' (HEADER, DELIMITER ',')")
                print(f"{name:<14} -> {path.name}")


if __name__ == "__main__":
    main()
