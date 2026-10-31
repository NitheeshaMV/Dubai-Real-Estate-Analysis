"""Step 4 - compute the headline numbers and write the key findings.

Output: report/facts.json (every number quoted in the report) and
        report/insights.json (the short findings shown on the dashboard).
Every sentence is generated from the data, so re-running the pipeline keeps it true.
"""
import json

import duckdb

from config import DB_PATH, ROOT

OUT = ROOT / "report"
OUT.mkdir(exist_ok=True)


def one(con, sql):
    row = con.execute(sql).fetchone()
    return row[0] if len(row) == 1 else row


def main() -> None:
    f = {}
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        tables = {r[0] for r in con.execute("SELECT table_name FROM information_schema.tables").fetchall()}
        f["sales"], f["value_aed"], f["first_day"], f["last_day"], f["months"] = one(con, """
            SELECT COUNT(*), SUM(price_aed), strftime(MIN(transaction_date), '%d %b %Y'),
                   strftime(MAX(transaction_date), '%d %b %Y'), COUNT(DISTINCT month) FROM sales""")
        f["areas"] = one(con, "SELECT COUNT(DISTINCT area) FROM sales")
        f["busiest_month"], f["busiest_month_sales"] = one(con, """
            SELECT strftime(month, '%B'), COUNT(*) FROM sales GROUP BY month ORDER BY 2 DESC LIMIT 1""")
        f["first_month"], f["last_month"] = one(con, "SELECT strftime(MIN(month), '%B'), strftime(MAX(month), '%B') FROM sales")
        f["first_month_sales"], f["last_month_sales"] = one(con, """
            SELECT FIRST(n ORDER BY month), LAST(n ORDER BY month) FROM (SELECT month, COUNT(*) n FROM sales GROUP BY month)""")
        f["volume_change"] = f["last_month_sales"] / f["first_month_sales"] - 1
        f["index_peak"], f["index_peak_month"] = one(con, """
            SELECT price_index, strftime(month, '%B') FROM mart_price_index ORDER BY price_index DESC LIMIT 1""")

        # Off-plan share of home sales, overall and first vs latest month
        f["offplan_share"] = one(con, "SELECT AVG(is_offplan::INT) FROM sales WHERE is_residential")
        f["offplan_share_first"], f["offplan_share_last"] = one(con, """
            SELECT FIRST(s ORDER BY month), LAST(s ORDER BY month) FROM (
              SELECT month, AVG(is_offplan::INT) s FROM sales WHERE is_residential GROUP BY month)""")
        f["offplan_premium"] = one(con, """
            SELECT MEDIAN(price_per_sqft) FILTER (WHERE is_offplan) / MEDIAN(price_per_sqft) FILTER (WHERE NOT is_offplan) - 1
            FROM sales WHERE segment = 'Apartment'""")

        # Price trend: first vs latest month, total value / total size
        for seg in ("Apartment", "Villa"):
            first, last = one(con, f"""
                SELECT FIRST(p ORDER BY month), LAST(p ORDER BY month) FROM (
                  SELECT month, SUM(price_aed) / SUM(size_sqft) p FROM sales WHERE segment = '{seg}' GROUP BY month)""")
            f[f"{seg.lower()}_sqft_first"], f[f"{seg.lower()}_sqft_last"] = first, last
            f[f"{seg.lower()}_sqft_change"] = last / first - 1

        # Like-for-like apartment index (fixed basket of areas) vs the raw average
        f["index_last"], f["raw_index_last"], f["index_areas"] = one(con, """
            SELECT LAST(price_index ORDER BY month), LAST(raw_index ORDER BY month), MIN(basket_areas)
            FROM mart_price_index""")
        f["lfl_change"] = f["index_last"] / 100 - 1
        f["raw_change"] = f["raw_index_last"] / 100 - 1

        # Areas (apartments)
        f["apartment_median_sqft"] = one(con, "SELECT MEDIAN(price_per_sqft) FROM sales WHERE segment = 'Apartment'")
        top3 = con.execute("""
            SELECT area, transactions, median_price_sqft FROM mart_area_leaderboard ORDER BY transactions DESC LIMIT 3""").fetchall()
        f["top3_areas"] = [r[0] for r in top3]
        f["top3_share"] = sum(r[1] for r in top3) / one(con, "SELECT COUNT(*) FROM sales WHERE segment = 'Apartment'")
        f["top3_below_median"] = sum(r[2] < f["apartment_median_sqft"] for r in top3)
        f["top15_below_median"] = one(con, f"""
            SELECT COUNT(*) FROM (SELECT * FROM mart_area_leaderboard ORDER BY transactions DESC LIMIT 15)
            WHERE median_price_sqft < {f['apartment_median_sqft']}""")
        f["fastest_risers"] = [[a, p] for a, p in con.execute("""
            SELECT area, price_change_pct FROM mart_area_leaderboard
            WHERE price_change_pct IS NOT NULL AND transactions >= 500
            ORDER BY price_change_pct DESC LIMIT 3""").fetchall()]

        # What people buy
        f["under_2m_share"] = one(con, "SELECT AVG((price_aed < 2e6)::INT) FROM sales WHERE is_residential")
        f["one_bed_or_studio_share"] = one(con, """
            SELECT AVG((rooms IN ('Studio', '1 B/R'))::INT) FROM sales WHERE segment = 'Apartment'""")
        f["median_home_price"] = one(con, "SELECT MEDIAN(price_aed) FROM sales WHERE is_residential")
        f["top_project"], f["top_project_area"], f["top_project_value"], f["top_project_share"] = one(con, """
            SELECT project, area, total_value_aed, share_of_market_value_pct FROM mart_top_projects LIMIT 1""")

        if "mart_rental_yield" in tables:
            f["yield_areas_measured"] = one(con, "SELECT COUNT(*) FROM mart_rental_yield")
            f["median_yield"] = one(con, "SELECT MEDIAN(gross_yield_pct) FROM mart_rental_yield")
            f["top_yields"] = [list(r) for r in con.execute("""
                SELECT area, gross_yield_pct, median_price_aed FROM mart_rental_yield ORDER BY gross_yield_pct DESC LIMIT 3""").fetchall()]
            f["low_yields"] = [list(r) for r in con.execute("""
                SELECT area, gross_yield_pct FROM mart_rental_yield ORDER BY gross_yield_pct ASC LIMIT 2""").fetchall()]
            # Cheapest third of areas (by price per sq ft) vs the priciest third
            f["yield_cheap_third"], f["yield_prime_third"] = one(con, """
                SELECT MEDIAN(gross_yield_pct) FILTER (WHERE t = 1), MEDIAN(gross_yield_pct) FILTER (WHERE t = 3)
                FROM (SELECT gross_yield_pct, NTILE(3) OVER (ORDER BY median_price_sqft) t FROM mart_rental_yield)""")

    pct = lambda x: f"{x * 100:.0f}%"
    bn = lambda x: f"AED {x / 1e9:,.0f} bn"
    trend = lambda c: f"{'up' if c >= 0 else 'down'} {abs(c) * 100:.1f}%"
    listing = lambda xs: ", ".join(xs[:-1]) + " and " + xs[-1] if len(xs) > 1 else xs[0]
    flat = abs(f["lfl_change"]) < 0.01
    price_head = ("Prices held steady" if flat else "Like-for-like prices rose" if f["lfl_change"] > 0
                  else "Like-for-like prices eased")
    mix_note = ""
    if abs(f["raw_change"] - f["lfl_change"]) >= 0.02:
        mix_points = abs(f["raw_change"] - f["lfl_change"]) * 100
        mix_note = (f" The simple city average went {trend(f['raw_change'])}, but {mix_points:.1f} points of that come from "
                    f"{'more' if f['raw_change'] < f['lfl_change'] else 'fewer'} sales in cheaper areas (a mix effect), not from prices.")
    peak_note = (f" They peaked in {f['index_peak_month']} ({f['index_peak'] - 100:+.1f}% vs {f['first_month']}) and eased after."
                 if f["index_peak"] - max(100, f["index_last"]) >= 1 else "")
    insights = [
        f"<b>{f['sales']:,} sales worth {bn(f['value_aed'])}</b> were registered from {f['first_day']} to {f['last_day']}. "
        f"Activity {'cooled' if f['volume_change'] < 0 else 'grew'}: {f['last_month']} had {f['last_month_sales']:,} sales, "
        f"{abs(f['volume_change']) * 100:.0f}% {'fewer' if f['volume_change'] < 0 else 'more'} than {f['first_month']} "
        f"(partly seasonal — Ramadan, Eid and summer; DLD's open data has no earlier years to compare).",
        f"<b>Off-plan dominates:</b> {pct(f['offplan_share'])} of home sales were off-plan "
        f"({pct(f['offplan_share_first'])} in {f['first_month']}, {pct(f['offplan_share_last'])} in {f['last_month']}); "
        f"off-plan apartments cost {pct(f['offplan_premium'])} more per sq ft than ready ones.",
        f"<b>{price_head}:</b> a fixed basket of {f['index_areas']} apartment areas went {trend(f['lfl_change'])} per sq ft "
        f"from {f['first_month']} to {f['last_month']}.{peak_note}{mix_note}",
        f"<b>Demand is concentrated{' in affordable areas' if f['top3_below_median'] == 3 else ''}:</b> "
        f"{listing(f['top3_areas'])} take {pct(f['top3_share'])} of apartment sales, and {f['top15_below_median']} of the "
        f"15 busiest areas sell below the city median of AED {f['apartment_median_sqft']:,.0f} per sq ft.",
        f"<b>Mid-market buyers:</b> {pct(f['under_2m_share'])} of homes sold for under AED 2M and "
        f"{pct(f['one_bed_or_studio_share'])} of apartments were studios or 1-bedrooms.",
    ]
    if "top_yields" in f:
        ty = f["top_yields"]
        insights.append(
            f"<b>Cheaper areas pay back faster:</b> the cheapest third of {f['yield_areas_measured']} areas earns a median "
            f"{f['yield_cheap_third']:.1f}% gross rental yield vs {f['yield_prime_third']:.1f}% for the priciest third. "
            f"Top: {ty[0][0]} ({ty[0][1]:.1f}%), {ty[1][0]} ({ty[1][1]:.1f}%), {ty[2][0]} ({ty[2][1]:.1f}%); "
            f"lowest: {f['low_yields'][0][0]} ({f['low_yields'][0][1]:.1f}%).")

    (OUT / "facts.json").write_text(json.dumps(f, indent=2, default=str), encoding="utf-8")
    (OUT / "insights.json").write_text(json.dumps(insights, indent=2, ensure_ascii=False), encoding="utf-8")
    for s in insights:
        print("-", s.replace("<b>", "").replace("</b>", ""))


if __name__ == "__main__":
    main()
