-- Top 25 HOME projects (apartments + villas) by sales value, with each project's rank inside its area.
-- Projects need 10+ sales: a single bulk deal (e.g. a whole plot sold for AED 3 bn) is not a "top project".
-- Land is excluded: some villa launches (e.g. The Oasis) are registered as land plots, see the README.
-- Skills shown: ROW_NUMBER() partitioned by area, share of total with a window SUM().
WITH project_stats AS (
    SELECT
        project,
        area,
        COUNT(*)                         AS transactions,
        SUM(price_aed)                   AS total_value_aed,
        MEDIAN(price_per_sqft)           AS median_price_sqft,
        AVG(CASE WHEN is_offplan THEN 1 ELSE 0 END) AS offplan_share
    FROM sales
    WHERE project IS NOT NULL AND is_residential
    GROUP BY project, area
    HAVING COUNT(*) >= 10
)
SELECT
    project,
    area,
    transactions,
    total_value_aed,
    ROUND(median_price_sqft, 0)                                         AS median_price_sqft,
    ROUND(offplan_share * 100, 1)                                       AS offplan_share_pct,
    ROUND(100.0 * total_value_aed / SUM(total_value_aed) OVER (), 2)    AS share_of_market_value_pct,
    ROW_NUMBER() OVER (PARTITION BY area ORDER BY total_value_aed DESC) AS rank_in_area
FROM project_stats
ORDER BY total_value_aed DESC
LIMIT 25;
