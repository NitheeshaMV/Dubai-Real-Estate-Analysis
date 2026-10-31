-- Monthly market pulse: volume, value, median price per sq ft and month-on-month change.
-- Skills shown: CTE, aggregation, window function LAG(), percentage change.
WITH monthly AS (
    SELECT
        month,
        COUNT(*)                              AS transactions,
        SUM(price_aed)                        AS total_value_aed,
        -- price metrics use homes only, so land plots do not distort them
        MEDIAN(price_aed)      FILTER (WHERE is_residential) AS median_price_aed,
        MEDIAN(price_per_sqft) FILTER (WHERE is_residential) AS median_price_sqft,
        AVG(CASE WHEN is_offplan THEN 1 ELSE 0 END) AS offplan_share
    FROM sales
    GROUP BY month
)
SELECT
    month,
    transactions,
    total_value_aed,
    median_price_aed,
    ROUND(median_price_sqft, 0)               AS median_price_sqft,
    ROUND(offplan_share * 100, 1)             AS offplan_share_pct,
    ROUND(100.0 * (transactions - LAG(transactions) OVER w)
          / NULLIF(LAG(transactions) OVER w, 0), 1)       AS volume_mom_pct,
    ROUND(100.0 * (median_price_sqft - LAG(median_price_sqft) OVER w)
          / NULLIF(LAG(median_price_sqft) OVER w, 0), 1)  AS price_sqft_mom_pct
FROM monthly
WINDOW w AS (ORDER BY month)
ORDER BY month;
