# Power BI report — how it is built

The report uses the star schema exported by `src/05_powerbi_model.py` (`powerbi/model/`) and the
measures in `DAX_measures.md`. Run `python run_all.py` first: it creates `powerbi/model/fact_sales.csv`
(not stored in the repository because of its size).

## 1. Load the data (10 min)
1. Open **Power BI Desktop** → **Get data → Text/CSV**.
2. Load all files from `powerbi/model/`: `fact_sales`, `dim_date`, `dim_area`, `dim_property`
   (and `fact_rent_yield` if it is there).
3. In **Power Query** check the types:
   - `fact_sales[date]`, `dim_date[date]` → Date
   - `price_aed`, `size_sqft`, `price_per_sqft` → Decimal number
   - `is_offplan`, `is_freehold` → True/False
   - all `*_key` columns → Whole number
4. **Close & Apply**.

## 2. Model view: build the star schema (10 min)
Create these relationships (one-to-many, single direction, from dimension to fact):

| From (one side) | To (many side) |
|---|---|
| `dim_date[date]` | `fact_sales[date]` |
| `dim_area[area_key]` | `fact_sales[area_key]` |
| `dim_property[property_key]` | `fact_sales[property_key]` |
| `dim_area[area]` | `fact_rent_yield[area]` *(optional)* |

Then select `dim_date` → **Table tools → Mark as date table** → column `date`.
Sort `dim_date[month_name]` by `month_number` (Column tools → Sort by column).

## 3. Measures (20 min)
Create the `_Measures` table and paste the measures from `DAX_measures.md`. Set the formats listed at the end of that file.

## 4. Report pages (60–90 min)

**Page 1 – Market overview**
- Title text box: "Dubai Property Market 2026" + subtitle "Source: Dubai Land Department Open Data".
- 5 cards: `Sales`, `Sales Value (AED)`, `Avg Price per Sq Ft`, `Off-plan Share %`, `Avg Deal Size (AED)`.
- Column chart: `dim_date[month_name]` × `Sales`.
- Line chart: `dim_date[month_name]` × `Avg Price per Sq Ft`, legend = `dim_property[segment]`, filter segment to Apartment and Villa.
- Stacked column: month × `Sales`, legend = `fact_sales[is_offplan]` (rename to Off-plan / Ready).
- Slicers (one row at the top): `dim_property[segment]`, `fact_sales[is_offplan]`, `dim_area[area]`.

**Page 2 – Areas**
- Table: `dim_area[area]`, `Sales`, `Sales Value (AED)`, `Avg Price per Sq Ft`, `Off-plan Share %`, `Area Rank by Sales`.
  Add conditional formatting (data bars) on `Sales`.
- Scatter: X = `Sales`, Y = `Avg Price per Sq Ft`, Values = `dim_area[area]` → the "value map".
- Bar chart: Top 15 areas by `Sales` (Filters pane → Top N = 15 by `Sales`).

**Page 3 – Buyers & projects**
- Bar: `dim_property[rooms]` × `Sales`.
- Column: `fact_sales[price_band]` × `Sales` (sort bands: Under 1M, 1-2M, 2-5M, 5-10M, 10M+).
- Table: `fact_sales[project]`, `dim_area[area]`, `Sales`, `Sales Value (AED)` → Top 10 by value.

**Page 4 – Rental yield** *(if `fact_rent_yield` is loaded)*
- Bar: `fact_rent_yield[area]` × `gross_yield_pct` (Top 15).
- Table with `median_price_aed`, `median_annual_rent_aed`, `years_of_rent_to_buy`.

## 5. Polish (15 min)
- One font (Segoe UI), one accent colour (blue `#2a78d6`), second series orange `#eb6834`.
- Same slicer row on every page (View → Sync slicers).
- Add a "Last refreshed" text box and the data source on every page.
- Save as `powerbi/Dubai_Real_Estate_2026.pbix`.

## 6. Share it
- Export **File → Export → PDF** → `powerbi/Dubai_Real_Estate_2026.pdf` (put it in the GitHub repo).
- Take 2–3 screenshots for the README and LinkedIn post.
- Personal Microsoft accounts cannot use "Publish to web"; the PDF + screenshots + the live HTML dashboard cover that.
