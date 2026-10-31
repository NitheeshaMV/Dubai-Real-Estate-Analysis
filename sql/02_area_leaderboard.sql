-- Apartment area leaderboard: demand, price level and price momentum (first quarter vs latest quarter).
-- Skills shown: multiple CTEs, conditional aggregation, RANK(), HAVING to avoid small samples.
WITH bounds AS (
    SELECT MIN(month) AS first_month, MAX(month) AS last_month FROM sales
),
area_stats AS (
    SELECT
        s.area,
        COUNT(*)                                   AS transactions,
        SUM(s.price_aed)                           AS total_value_aed,
        MEDIAN(s.price_aed)                        AS median_price_aed,
        MEDIAN(s.price_per_sqft)                   AS median_price_sqft,
        AVG(CASE WHEN s.is_offplan THEN 1 ELSE 0 END) AS offplan_share,
        MEDIAN(s.price_per_sqft) FILTER (WHERE s.month <  b.first_month + INTERVAL 3 MONTH) AS early_price_sqft,
        MEDIAN(s.price_per_sqft) FILTER (WHERE s.month >  b.last_month  - INTERVAL 3 MONTH) AS late_price_sqft,
        COUNT(*) FILTER (WHERE s.month <  b.first_month + INTERVAL 3 MONTH) AS early_n,
        COUNT(*) FILTER (WHERE s.month >  b.last_month  - INTERVAL 3 MONTH) AS late_n
    FROM sales s CROSS JOIN bounds b
    WHERE s.segment = 'Apartment'
    GROUP BY s.area
    HAVING COUNT(*) >= 200
)
SELECT
    area,
    transactions,
    total_value_aed,
    median_price_aed,
    ROUND(median_price_sqft, 0)                                   AS median_price_sqft,
    ROUND(offplan_share * 100, 1)                                 AS offplan_share_pct,
    CASE WHEN early_n >= 30 AND late_n >= 30
         THEN ROUND(100.0 * (late_price_sqft - early_price_sqft) / early_price_sqft, 1)
    END                                                           AS price_change_pct,
    RANK() OVER (ORDER BY transactions DESC)                      AS demand_rank,
    RANK() OVER (ORDER BY median_price_sqft DESC)                 AS price_rank
FROM area_stats
ORDER BY transactions DESC;
