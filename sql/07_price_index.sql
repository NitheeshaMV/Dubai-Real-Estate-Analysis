-- Like-for-like apartment price index (first month = 100).
-- A plain city-wide average moves when the MIX of areas changes (more sales in cheap areas
-- pulls it down even if no price fell). This index fixes the basket: only areas with enough
-- sales in every month, each weighted by its share of sales over the whole period.
-- Skills shown: multi-step CTEs, fixed-weight (Laspeyres-style) index, FIRST_VALUE() window.
WITH area_month AS (
    SELECT area, month, COUNT(*) AS n, SUM(price_aed) / SUM(size_sqft) AS price_sqft
    FROM sales
    WHERE segment = 'Apartment'
    GROUP BY area, month
),
basket AS (                      -- areas present with 20+ sales in every month
    SELECT area, SUM(n) AS weight
    FROM area_month
    GROUP BY area
    HAVING COUNT(*) = (SELECT COUNT(DISTINCT month) FROM sales) AND MIN(n) >= 20
),
weighted AS (
    SELECT m.month,
           SUM(b.weight * m.price_sqft) / SUM(b.weight) AS basket_price_sqft,
           COUNT(*)                                      AS basket_areas
    FROM area_month m JOIN basket b USING (area)
    GROUP BY m.month
),
raw AS (
    SELECT month, SUM(price_aed) / SUM(size_sqft) AS raw_avg_price_sqft
    FROM sales WHERE segment = 'Apartment' GROUP BY month
)
SELECT
    w.month,
    w.basket_areas,
    ROUND(w.basket_price_sqft, 0)                                                     AS like_for_like_price_sqft,
    ROUND(100 * w.basket_price_sqft / FIRST_VALUE(w.basket_price_sqft) OVER (ORDER BY w.month), 1) AS price_index,
    ROUND(r.raw_avg_price_sqft, 0)                                                    AS raw_avg_price_sqft,
    ROUND(100 * r.raw_avg_price_sqft / FIRST_VALUE(r.raw_avg_price_sqft) OVER (ORDER BY w.month), 1) AS raw_index
FROM weighted w JOIN raw r USING (month)
ORDER BY w.month;
