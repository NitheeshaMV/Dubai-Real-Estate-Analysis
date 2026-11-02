-- Gross rental yield by area for apartments, matched on the SAME BUILDINGS.
-- DLD's rent records use official land-area names ("Al Barsha South Fourth") while sales use
-- community names ("Jumeirah Village Circle"), so areas cannot be joined directly. The building
-- (project) name appears in both: each building is mapped to its sales area, and only buildings
-- with both ready sales and new leases are used — rent and price come from the same buildings.
-- Gross yield = median annual rent per sq ft ÷ median sale price per sq ft (ready apartments only,
-- so off-plan premiums do not distort it).
-- Net yield = (rent per sq ft − annual service charge per sq ft) ÷ price per sq ft. The service charge is the
-- 2026 RERA-approved rate (DLD Service Charge Index) of the area's most-leased building in the index, so it is
-- net of service charges only — not of vacancy, maintenance inside the unit or agency fees.
-- Skills shown: bridge table between two sources, multi-CTE join, sample-size guards, LEFT JOIN to a lookup, RANK().
WITH building_area AS (          -- the sales area each building belongs to
    SELECT project, MODE(area) AS area
    FROM sales
    WHERE segment = 'Apartment' AND project IS NOT NULL
    GROUP BY project
),
ready_sales AS (
    SELECT b.area, s.project, s.price_aed, s.price_per_sqft
    FROM sales s JOIN building_area b USING (project)
    WHERE s.segment = 'Apartment' AND NOT s.is_offplan
),
leases AS (
    SELECT b.area, r.project, r.annual_rent_aed, r.rent_per_sqft
    FROM rents r JOIN building_area b USING (project)
    WHERE r.segment = 'Apartment' AND r.contract_type = 'New'
),
matched AS (                     -- buildings present on both sides
    SELECT DISTINCT project FROM ready_sales
    INTERSECT
    SELECT DISTINCT project FROM leases
),
sale AS (
    SELECT area, COUNT(*) AS ready_sales, COUNT(DISTINCT project) AS buildings,
           MEDIAN(price_aed) AS median_price_aed, MEDIAN(price_per_sqft) AS median_price_sqft
    FROM ready_sales WHERE project IN (SELECT project FROM matched)
    GROUP BY area HAVING COUNT(*) >= 50 AND COUNT(DISTINCT project) >= 3   -- not decided by 1-2 towers
),
rent AS (
    SELECT area, COUNT(*) AS leases,
           MEDIAN(annual_rent_aed) AS median_annual_rent_aed, MEDIAN(rent_per_sqft) AS median_rent_sqft
    FROM leases WHERE project IN (SELECT project FROM matched)
    GROUP BY area HAVING COUNT(*) >= 50
)
SELECT
    area,
    buildings,
    ready_sales,
    leases,
    ROUND(median_price_aed, 0)                             AS median_price_aed,
    ROUND(median_annual_rent_aed, 0)                       AS median_annual_rent_aed,
    ROUND(median_price_sqft, 0)                            AS median_price_sqft,
    ROUND(median_rent_sqft, 1)                             AS median_rent_sqft,
    ROUND(100.0 * median_rent_sqft / median_price_sqft, 2) AS gross_yield_pct,
    ROUND(median_price_sqft / median_rent_sqft, 1)         AS years_of_rent_to_buy,
    RANK() OVER (ORDER BY median_rent_sqft / median_price_sqft DESC) AS yield_rank,
    sc.dld_project                                         AS service_charge_building,
    sc.service_charge_aed_sqft,
    ROUND(100.0 * (median_rent_sqft - sc.service_charge_aed_sqft) / median_price_sqft, 2) AS net_yield_pct,
    ROUND(100.0 * sc.service_charge_aed_sqft / median_rent_sqft, 1)                     AS service_charge_share_of_rent_pct
FROM sale JOIN rent USING (area)
LEFT JOIN service_charges sc USING (area)         -- areas without an index entry keep gross yield only
ORDER BY gross_yield_pct DESC;
