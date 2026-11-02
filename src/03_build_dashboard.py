"""Step 3 - build the self-contained interactive dashboard (dashboard/index.html).

The page needs no server: aggregated data is embedded as JSON and charts are drawn
in the browser with Chart.js, so it can be hosted for free on GitHub Pages.
"""
import json

import duckdb

from config import DASHBOARD_DIR, DB_PATH, ROOT

TEMPLATE = DASHBOARD_DIR / "template.html"
OUTPUT = DASHBOARD_DIR / "index.html"
INSIGHTS = ROOT / "report" / "insights.json"


def main() -> None:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        months = [r[0] for r in con.execute(
            "SELECT DISTINCT strftime(month, '%Y-%m') FROM sales ORDER BY 1").fetchall()]
        areas = [r[0] for r in con.execute(
            "SELECT area FROM sales WHERE area IS NOT NULL GROUP BY area ORDER BY COUNT(*) DESC").fetchall()]
        segments = ["Apartment", "Villa", "Commercial", "Hotel", "Land", "Other"]
        rooms = [r[0] for r in con.execute(
            "SELECT rooms FROM sales GROUP BY rooms ORDER BY COUNT(*) DESC").fetchall()]

        idx = lambda values: {v: i for i, v in enumerate(values)}
        m_i, a_i, s_i, r_i = idx(months), idx(areas), idx(segments), idx(rooms)

        # One row per month x area x segment x off-plan x rooms. Sums (not medians) so
        # any filter combination can be re-aggregated in the browser.
        cube = [
            [m_i[m], a_i[a], s_i[s], int(o), r_i[r], n, round(v), round(sq)]
            for m, a, s, o, r, n, v, sq in con.execute("""
                SELECT strftime(month, '%Y-%m'), area, segment, is_offplan, rooms,
                       COUNT(*), SUM(price_aed), SUM(size_sqft)
                FROM sales WHERE area IS NOT NULL
                GROUP BY ALL""").fetchall()
        ]
        projects = [
            [p, a_i[a], s_i[s], int(o), n, round(v), round(sq)]
            for p, a, s, o, n, v, sq in con.execute("""
                SELECT project, area, segment, is_offplan,
                       COUNT(*), SUM(price_aed), SUM(size_sqft)
                FROM sales WHERE project IS NOT NULL AND area IS NOT NULL
                GROUP BY ALL HAVING COUNT(*) >= 10""").fetchall()
        ]
        has_yield = con.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'mart_rental_yield'").fetchone()[0]
        rental_yield = [list(r) for r in con.execute("""
            SELECT area, ready_sales, leases, median_price_aed, median_annual_rent_aed, gross_yield_pct, years_of_rent_to_buy, buildings,
                   net_yield_pct, service_charge_aed_sqft, service_charge_share_of_rent_pct
            FROM mart_rental_yield ORDER BY gross_yield_pct DESC""").fetchall()] if has_yield else []
        rent_period = con.execute("""
            SELECT strftime(MIN(registration_date), '%d %b') || ' – ' || strftime(MAX(registration_date), '%d %b %Y')
            FROM rents""").fetchone()[0] if has_yield else ""
        price_index = [list(r) for r in con.execute("""
            SELECT strftime(month, '%Y-%m'), price_index, raw_index, basket_areas
            FROM mart_price_index ORDER BY month""").fetchall()]
        first, last, last_month_complete = con.execute("""
            SELECT strftime(MIN(transaction_date), '%d %b %Y'), strftime(MAX(transaction_date), '%d %b %Y'),
                   day(MAX(transaction_date)) = day(last_day(MAX(transaction_date))) FROM sales""").fetchone()

    data = {
        "months": months, "areas": areas, "segments": segments, "rooms": rooms,
        "cube": cube, "projects": projects, "priceIndex": price_index,
        "rentalYield": rental_yield, "rentPeriod": rent_period,
        "period": f"{first} – {last}",
        "lastMonthComplete": bool(last_month_complete),
    }
    # Key findings written by 04_insights.py (shown under the charts when present).
    insights = json.loads(INSIGHTS.read_text(encoding="utf-8")) if INSIGHTS.exists() else []
    html = (TEMPLATE.read_text(encoding="utf-8")
            .replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":"), ensure_ascii=False))
            .replace("/*__INSIGHTS__*/[]", json.dumps(insights, ensure_ascii=False)))
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUTPUT} ({OUTPUT.stat().st_size / 1e6:.1f} MB, {len(cube):,} cube rows, {len(projects):,} projects)")


if __name__ == "__main__":
    main()
