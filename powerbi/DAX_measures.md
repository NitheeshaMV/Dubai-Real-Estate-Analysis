# DAX measures

Create these in a `_Measures` table (Home → Enter data → name it `_Measures`, then delete its column).
Every measure is written against the star schema in `powerbi/model/`.

## Core

```DAX
Sales = COUNTROWS ( fact_sales )

Sales Value (AED) = SUM ( fact_sales[price_aed] )

Avg Price per Sq Ft =
DIVIDE ( SUM ( fact_sales[price_aed] ), SUM ( fact_sales[size_sqft] ) )

Median Price (AED) = MEDIAN ( fact_sales[price_aed] )

Avg Deal Size (AED) = DIVIDE ( [Sales Value (AED)], [Sales] )
```

## Off-plan

```DAX
Off-plan Sales =
CALCULATE ( [Sales], fact_sales[is_offplan] = TRUE () )

Off-plan Share % = DIVIDE ( [Off-plan Sales], [Sales] )

Off-plan Premium % =
VAR OffPlan = CALCULATE ( [Avg Price per Sq Ft], fact_sales[is_offplan] = TRUE () )
VAR Ready   = CALCULATE ( [Avg Price per Sq Ft], fact_sales[is_offplan] = FALSE () )
RETURN DIVIDE ( OffPlan - Ready, Ready )
```

## Time intelligence (needs `dim_date` marked as the date table)

```DAX
Sales Prev Month =
CALCULATE ( [Sales], DATEADD ( dim_date[date], -1, MONTH ) )

Sales MoM % = DIVIDE ( [Sales] - [Sales Prev Month], [Sales Prev Month] )

Price per Sq Ft Prev Month =
CALCULATE ( [Avg Price per Sq Ft], DATEADD ( dim_date[date], -1, MONTH ) )

Price MoM % =
DIVIDE ( [Avg Price per Sq Ft] - [Price per Sq Ft Prev Month], [Price per Sq Ft Prev Month] )

Sales YTD = TOTALYTD ( [Sales], dim_date[date] )

Sales 3M Rolling =
CALCULATE ( [Sales], DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -3, MONTH ) )
```

## Ranking (for the area table and Top N visuals)

```DAX
Area Rank by Sales =
IF (
    HASONEVALUE ( dim_area[area] ),
    RANKX ( ALLSELECTED ( dim_area[area] ), [Sales], , DESC, DENSE )
)

Share of Market Value % =
DIVIDE ( [Sales Value (AED)], CALCULATE ( [Sales Value (AED)], ALLSELECTED ( dim_area ) ) )
```

## Rental yield (only if `fact_rent_yield.csv` was loaded)

```DAX
Gross Yield % = AVERAGE ( fact_rent_yield[gross_yield_pct] ) / 100

Years of Rent to Buy = AVERAGE ( fact_rent_yield[years_of_rent_to_buy] )
```

## Formatting tips
- `Sales Value (AED)` → Format: Decimal number, Display units: Billions, 1 decimal.
- `Avg Price per Sq Ft` → Whole number, thousands separator.
- All `%` measures → Percentage, 1 decimal.
