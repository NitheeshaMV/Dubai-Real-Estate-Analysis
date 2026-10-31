-- Buyer segments: what people buy (property sub-type x bedrooms) and at which price band.
-- Skills shown: GROUPING SETS for several summaries in one pass.
SELECT
    COALESCE(segment, 'All')    AS segment,
    COALESCE(rooms, 'All')      AS rooms,
    COALESCE(price_band, 'All') AS price_band,
    COUNT(*)                    AS transactions,
    ROUND(MEDIAN(price_aed), 0) AS median_price_aed,
    ROUND(MEDIAN(size_sqft), 0) AS median_size_sqft,
    ROUND(MEDIAN(price_per_sqft), 0) AS median_price_sqft
FROM sales
WHERE is_residential
GROUP BY GROUPING SETS ((segment, rooms), (price_band), (segment))
HAVING COUNT(*) >= 50
ORDER BY transactions DESC;
