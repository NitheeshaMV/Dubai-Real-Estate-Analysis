# Dubai Property Market, Jan–Sep 2026 — Insights & Recommendations

**Nitheesha M V** · Source: Dubai Land Department open data · **121,741 sales worth AED 376 bn**, 1 Jan – 30 Sep 2026
(apartments 95,510 · villas 9,481 · land 9,409 · commercial 4,861 · hotel 2,455) · plus **34,649 new residential leases** (Ejari, September 2026)

## The headline
Dubai's market is still large but **cooling**: fewer sales each month, prices **easing slightly** since an April
peak, and buyers concentrating in **affordable, mostly off-plan** communities — which are also where rental
yields are highest. The simple city-wide average price makes the slowdown look five times worse than it is.

## Key findings

**1. Activity cooled through the year.** Monthly sales fell from 17,192 in January to 11,038 in September (−36%).
Part of this is seasonal (Ramadan in March, Eid in May, summer); DLD's open data has no earlier years to confirm how much.

**2. Three in four home sales are off-plan — and off-plan buyers get less space for their money.**
75% of home sales were off-plan, peaking at 79.5% in April and easing to 71.5% in September.
The median off-plan apartment costs about 8% more than the median ready one (AED 1.25M vs 1.15M) but
**26% more per sq ft** (AED 1,772 vs 1,405) — buyers pay for future delivery with smaller homes.

**3. Prices eased only 2.3% — the "12% drop" is a mix effect.** A like-for-like index of 47 apartment areas
(same areas, fixed weights) rose to +4.1% in April, then eased to −2.3% by September (−6.1% from the peak).
The simple average fell 12.4%, but 10.1 points of that are because more sales happened in cheaper areas.
*Reading the simple average would overstate the price fall about 5×.*

**4. Demand is concentrated in affordable communities.** Madinat Al Mataar (11,242 apartment sales, 100% off-plan,
median AED 773k), Jumeirah Village Circle (7,156) and Dubai Land Residence Complex (4,755) take **24% of all
apartment sales**. 10 of the 15 busiest areas sell below the city median of AED 1,714 per sq ft.

**5. The core buyer is mid-market.** 68% of homes sold for under AED 2M; 71% of apartments sold were studios
(median AED 673k) or 1-bedrooms (median AED 1.25M).

**6. Area momentum differs sharply** (median price per sq ft, Jan–Mar vs Jul–Sep, areas with 500+ sales):
rising — Down Town Jabal Ali +26%, Damac Hills +16%, Jabal Ali First +11%, Madinat Al Mataar +8%;
falling — Business Bay −20%, Palm Jumeirah −19%, Al Hebiah First −15%.
*Caveat:* inside one area, a luxury launch early in the year can move the median on its own — check the project mix before acting.

**7. Cheaper areas pay back faster.** Gross rental yield for apartments across 35 areas (rent and price from the
same buildings) has a median of 7.2%. The cheapest third of areas earns a median **8.3%** vs **5.4%** for the priciest third.
Highest: Dubai Investment Park Second 9.7%, Dubai Land Residence Complex 9.3%, Dubai Production City 9.3%, Majan 9.2%,
International City Ph 1 9.0%. Lowest: Palm Jumeirah 4.7%, Dubai Harbour 4.8%, La Mer 4.9%.
In years of rent needed to pay the price: ~11 years in the top areas vs ~21 on Palm Jumeirah.

**Top home projects by sales value:** LUNAYA (Saih Shuaib 1, AED 3.2 bn), Hado by Beyond (Palm Deira, AED 2.5 bn),
Creek Bay (Al Khairan First, AED 2.2 bn) — all 100% off-plan.

## Recommendations

**For home buyers**
- **Look at ready homes first if you need to move in:** ready apartments are ~21% cheaper per sq ft than off-plan.
  High-demand, below-median areas where 35–40% of sales are ready homes: Jumeirah Village Circle, Arjan, Dubai Sports City.
- **Negotiate:** like-for-like prices are 6.1% below the April peak and still easing.

**For investors**
- **For rental income, go affordable:** Dubai Production City, Dubai Land Residence Complex, Majan, International City
  and Silicon Oasis yield 8–9% gross; Jumeirah Village Circle (the deepest market, 168 buildings) yields 7.2%.
- **Prime areas (Palm Jumeirah, Dubai Harbour, La Mer: under 5%) only work as a bet on price growth** — and Palm Jumeirah's
  median price per sq ft fell this year, so check the project mix before buying there.
- **Prefer areas with both liquidity and rising prices** — easier to resell: Madinat Al Mataar, Jabal Ali First, Dubai Production City.
- **Justify the 26% off-plan premium** with the payment plan and expected growth; with prices easing, ready units carry less risk.
- **Check before buying in falling areas** (Business Bay, Palm Jumeirah): confirm whether the drop is real or a launch-mix effect.

**For brokers and developers**
- **Focus inventory and marketing on studios/1-bedrooms under AED 2M** — that is 7 in 10 apartment deals.
- **Build resale listings:** the off-plan share slipped from 79.5% (April) to 71.5% (September); the ready/secondary market is gaining share.
- **Report like-for-like prices to clients**, not simple averages — it avoids alarming (or over-selling) buyers.

## Method
DLD CSV exports → Python cleaning (dedupe, segment mapping, outlier rules) → DuckDB SQL marts → notebook,
interactive dashboard and Power BI model. Details: [README](../README.md) · [Notebook](../notebooks/dubai_real_estate_analysis.ipynb).

## Limitations and next steps
- Current-year data only → no year-on-year comparison or seasonality adjustment. *Next:* add 2024–2025 from Dubai Pulse.
- Some villa launches (e.g. Mareva at The Oasis, Eden Hills) are registered as land plots, so off-plan villa activity is understated.
- Rent records name areas differently from sales (official land areas vs communities), so yields are matched through
  building names; leases cover one month (September) and yields are gross. *Next:* more months of leases, net yields
  (service charges), and a 6-month price forecast.

*Personal portfolio project on public data. Not investment advice.*
