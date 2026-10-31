-- Off-plan vs ready: how much of the market is sold before completion, and the price gap.
-- Skills shown: GROUP BY with ROLLUP-free pivot via FILTER, share-of-total window.
SELECT
    month,
    COUNT(*) FILTER (WHERE is_offplan)                         AS offplan_transactions,
    COUNT(*) FILTER (WHERE NOT is_offplan)                     AS ready_transactions,
    ROUND(MEDIAN(price_per_sqft) FILTER (WHERE is_offplan), 0)     AS offplan_median_sqft,
    ROUND(MEDIAN(price_per_sqft) FILTER (WHERE NOT is_offplan), 0) AS ready_median_sqft,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_offplan) / COUNT(*), 1) AS offplan_share_pct
FROM sales
WHERE is_residential
GROUP BY month
ORDER BY month;
