"""Step 6 - generate the Power BI Project (powerbi/Dubai_Real_Estate_2026.pbip).

A .pbip is Power BI Desktop's text format: the semantic model (tables, relationships, DAX
measures) as model.bim and the report pages as report.json. Open the .pbip in Power BI
Desktop, click Refresh, then File -> Save as -> .pbix.
"""
import json

from config import POWERBI_DIR

NAME = "Dubai_Real_Estate_2026"
MODEL_DIR = POWERBI_DIR / "model"
SM = POWERBI_DIR / f"{NAME}.SemanticModel"
RP = POWERBI_DIR / f"{NAME}.Report"

BLUE, ORANGE = "#2a78d6", "#eb6834"

# ---------------------------------------------------------------- semantic model
# (column, dataType, M type, format, summarizeBy)
TABLES = {
    "fact_sales": [
        ("transaction_id", "string", "type text", None, "none"),
        ("date", "dateTime", "type date", "dd mmm yyyy", "none"),
        ("area_key", "int64", "Int64.Type", "0", "none"),
        ("property_key", "int64", "Int64.Type", "0", "none"),
        ("project", "string", "type text", None, "none"),
        ("procedure", "string", "type text", None, "none"),
        ("is_offplan", "boolean", "type logical", None, "none"),
        ("registration", "string", "type text", None, "none"),
        ("is_freehold", "boolean", "type logical", None, "none"),
        ("price_aed", "double", "type number", "#,0", "sum"),
        ("size_sqft", "double", "type number", "#,0", "sum"),
        ("price_per_sqft", "double", "type number", "#,0", "none"),
        ("price_band", "string", "type text", None, "none"),
        ("price_band_order", "int64", "Int64.Type", "0", "none"),
    ],
    "dim_date": [
        ("date", "dateTime", "type date", "dd mmm yyyy", "none"),
        ("year", "int64", "Int64.Type", "0", "none"),
        ("quarter", "int64", "Int64.Type", "0", "none"),
        ("month_number", "int64", "Int64.Type", "0", "none"),
        ("month_name", "string", "type text", None, "none"),
        ("year_month", "string", "type text", None, "none"),
        ("week", "int64", "Int64.Type", "0", "none"),
        ("weekday", "string", "type text", None, "none"),
    ],
    "dim_area": [
        ("area_key", "int64", "Int64.Type", "0", "none"),
        ("area", "string", "type text", None, "none"),
        ("nearest_metro", "string", "type text", None, "none"),
        ("nearest_mall", "string", "type text", None, "none"),
        ("nearest_landmark", "string", "type text", None, "none"),
    ],
    "dim_property": [
        ("property_key", "int64", "Int64.Type", "0", "none"),
        ("segment", "string", "type text", None, "none"),
        ("property_type", "string", "type text", None, "none"),
        ("property_sub_type", "string", "type text", None, "none"),
        ("rooms", "string", "type text", None, "none"),
    ],
    "fact_rent_yield": [
        ("area", "string", "type text", None, "none"),
        ("buildings", "int64", "Int64.Type", "#,0", "sum"),
        ("ready_sales", "int64", "Int64.Type", "#,0", "sum"),
        ("leases", "int64", "Int64.Type", "#,0", "sum"),
        ("median_price_aed", "double", "type number", "#,0", "none"),
        ("median_annual_rent_aed", "double", "type number", "#,0", "none"),
        ("median_price_sqft", "double", "type number", "#,0", "none"),
        ("median_rent_sqft", "double", "type number", "#,0.0", "none"),
        ("gross_yield_pct", "double", "type number", "0.00", "none"),
        ("years_of_rent_to_buy", "double", "type number", "0.0", "none"),
        ("yield_rank", "int64", "Int64.Type", "0", "none"),
        ("median_price_aed_m", "double", "type number", "0.00", "none"),
        ("median_annual_rent_aed_k", "double", "type number", "0.0", "none"),
    ],
    "fact_price_index": [
        ("month", "dateTime", "type date", "mmm yyyy", "none"),
        ("basket_areas", "int64", "Int64.Type", "0", "none"),
        ("like_for_like_price_sqft", "double", "type number", "#,0", "none"),
        ("price_index", "double", "type number", "0.0", "none"),
        ("raw_avg_price_sqft", "double", "type number", "#,0", "none"),
        ("raw_index", "double", "type number", "0.0", "none"),
    ],
}

MEASURES = [  # (name, DAX, format)
    ("Sales", "COUNTROWS ( fact_sales )", "#,0"),
    ("Sales Value (AED)", "SUM ( fact_sales[price_aed] )", "#,0"),
    # Scaled versions for tables: they read the same whatever the PC's digit grouping (e.g. Indian lakh/crore)
    ("Value (AED bn)", "DIVIDE ( [Sales Value (AED)], 1e9 )", "0.00"),
    ("Avg Deal (AED M)", "DIVIDE ( [Avg Deal Size (AED)], 1e6 )", "0.00"),
    ("Avg Price per Sq Ft", "DIVIDE ( SUM ( fact_sales[price_aed] ), SUM ( fact_sales[size_sqft] ) )", "#,0"),
    ("Median Price (AED)", "MEDIAN ( fact_sales[price_aed] )", "#,0"),
    ("Avg Deal Size (AED)", "DIVIDE ( [Sales Value (AED)], [Sales] )", "#,0"),
    ("Off-plan Sales", "CALCULATE ( [Sales], fact_sales[is_offplan] = TRUE () )", "#,0"),
    ("Off-plan Share %", "DIVIDE ( [Off-plan Sales], [Sales] )", "0.0%"),
    ("Off-plan Premium %",
     "VAR OffPlan = CALCULATE ( [Avg Price per Sq Ft], fact_sales[is_offplan] = TRUE () )\n"
     "VAR Ready = CALCULATE ( [Avg Price per Sq Ft], fact_sales[is_offplan] = FALSE () )\n"
     "RETURN DIVIDE ( OffPlan - Ready, Ready )", "0.0%"),
    ("Sales Prev Month", "CALCULATE ( [Sales], DATEADD ( dim_date[date], -1, MONTH ) )", "#,0"),
    ("Sales MoM %", "DIVIDE ( [Sales] - [Sales Prev Month], [Sales Prev Month] )", "0.0%"),
    ("Price per Sq Ft Prev Month", "CALCULATE ( [Avg Price per Sq Ft], DATEADD ( dim_date[date], -1, MONTH ) )", "#,0"),
    ("Price MoM %", "DIVIDE ( [Avg Price per Sq Ft] - [Price per Sq Ft Prev Month], [Price per Sq Ft Prev Month] )", "0.0%"),
    ("Sales YTD", "TOTALYTD ( [Sales], dim_date[date] )", "#,0"),
    ("Sales 3M Rolling", "CALCULATE ( [Sales], DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -3, MONTH ) )", "#,0"),
    ("Area Rank by Sales",
     "IF ( HASONEVALUE ( dim_area[area] ), RANKX ( ALLSELECTED ( dim_area[area] ), [Sales], , DESC, DENSE ) )", "0"),
    ("Share of Market Value %",
     "DIVIDE ( [Sales Value (AED)], CALCULATE ( [Sales Value (AED)], ALLSELECTED ( dim_area ) ) )", "0.0%"),
    ("Gross Yield %", "AVERAGE ( fact_rent_yield[gross_yield_pct] ) / 100", "0.0%"),
    ("Years of Rent to Buy", "AVERAGE ( fact_rent_yield[years_of_rent_to_buy] )", "0.0"),
    ("Like-for-like Index", "AVERAGE ( fact_price_index[price_index] )", "0.0"),
    ("Simple Average Index", "AVERAGE ( fact_price_index[raw_index] )", "0.0"),
    # KPI cards for the price-index, buyers and rental-yield pages
    ("Like-for-like Change %",
     "VAR LastMonth = CALCULATE ( MAX ( fact_price_index[month] ), ALL ( fact_price_index ) )\n"
     "RETURN DIVIDE ( CALCULATE ( AVERAGE ( fact_price_index[price_index] ), fact_price_index[month] = LastMonth, "
     "ALL ( fact_price_index ) ), 100 ) - 1", "+0.0%;-0.0%;0.0%"),
    ("Simple Average Change %",
     "VAR LastMonth = CALCULATE ( MAX ( fact_price_index[month] ), ALL ( fact_price_index ) )\n"
     "RETURN DIVIDE ( CALCULATE ( AVERAGE ( fact_price_index[raw_index] ), fact_price_index[month] = LastMonth, "
     "ALL ( fact_price_index ) ), 100 ) - 1", "+0.0%;-0.0%;0.0%"),
    ("Mix Effect (index points)", "( [Simple Average Change %] - [Like-for-like Change %] ) * 100", "+0.0;-0.0;0.0"),
    ("Share Under AED 2M", "DIVIDE ( CALCULATE ( [Sales], fact_sales[price_band_order] <= 2 ), [Sales] )", "0%"),
    ("Studios & 1-Beds Share",
     'DIVIDE ( CALCULATE ( [Sales], dim_property[rooms] IN { "Studio", "1 B/R" } ), [Sales] )', "0%"),
    ("Median Gross Yield", "MEDIAN ( fact_rent_yield[gross_yield_pct] ) / 100", "0.0%"),
    ("Best Gross Yield", "MAX ( fact_rent_yield[gross_yield_pct] ) / 100", "0.0%"),
    ("Areas Measured", "COUNTROWS ( fact_rent_yield )", "0"),
    ("Median Price (AED M)", "DIVIDE ( [Median Price (AED)], 1e6 )", "0.00"),
]

RELATIONSHIPS = [  # (many table, column, one table, column)
    ("fact_sales", "date", "dim_date", "date"),
    ("fact_sales", "area_key", "dim_area", "area_key"),
    ("fact_sales", "property_key", "dim_property", "property_key"),
    ("fact_rent_yield", "area", "dim_area", "area"),
    ("fact_price_index", "month", "dim_date", "date"),
]


def m_query(table: str, cols) -> list[str]:
    types = ", ".join(f'{{"{c}", {m}}}' for c, _, m, _, _ in cols)
    return [
        "let",
        f'    Source = Csv.Document(File.Contents(DataFolder & "{table}.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
        f'    Typed = Table.TransformColumnTypes(Promoted, {{{types}}}, "en-US")',
        "in",
        "    Typed",
    ]


def build_model() -> dict:
    tables = []
    for name, cols in TABLES.items():
        t = {
            "name": name,
            "columns": [
                {"name": c, "dataType": dt, "sourceColumn": c, "summarizeBy": sb,
                 **({"formatString": fmt} if fmt else {})}
                for c, dt, _, fmt, sb in cols
            ],
            "partitions": [{"name": name, "mode": "import", "source": {"type": "m", "expression": m_query(name, cols)}}],
        }
        if name == "dim_date":                       # mark as the date table
            t["dataCategory"] = "Time"
            for c in t["columns"]:
                if c["name"] == "date":
                    c["isKey"] = True
                if c["name"] == "month_name":
                    c["sortByColumn"] = "month_number"
        if name == "fact_sales":
            for c in t["columns"]:
                if c["name"] == "price_band":
                    c["sortByColumn"] = "price_band_order"
                if c["name"] in ("area_key", "property_key", "price_band_order"):
                    c["isHidden"] = True
        if name in ("dim_area", "dim_property"):
            t["columns"][0]["isHidden"] = True       # surrogate keys
        tables.append(t)
    tables.append({
        "name": "_Measures",
        "columns": [{"name": "Column1", "dataType": "string", "sourceColumn": "Column1", "isHidden": True, "summarizeBy": "none"}],
        "partitions": [{"name": "_Measures", "mode": "import", "source": {
            "type": "m", "expression": ["let", '    Source = #table(type table [Column1 = text], {})', "in", "    Source"]}}],
        "measures": [{"name": n, "expression": e.split("\n"), "formatString": fmt} for n, e, fmt in MEASURES],
    })
    data_folder = str(MODEL_DIR) + "\\"
    return {
        "compatibilityLevel": 1567,
        "model": {
            "culture": "en-US",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "tables": tables,
            "relationships": [
                {"name": f"{a}_{b}_{c}", "fromTable": a, "fromColumn": b, "toTable": c, "toColumn": d}
                for a, b, c, d in RELATIONSHIPS
            ],
            "expressions": [{
                "name": "DataFolder", "kind": "m",
                "expression": f'"{data_folder}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]',
            }],
            "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps(["DataFolder", *TABLES, "_Measures"])}],
        },
    }


# ---------------------------------------------------------------- report
# Design system: navy header band with page navigation, light-grey canvas, white rounded cards on a
# 20 px margin / 12 px gutter grid. Most styling lives in the theme (visualStyles) so every visual
# matches; visuals only carry what is specific to them (titles, data labels, sort order).
NAVY, CANVAS, CARD_BORDER, INK, MUTED = "#12325B", "#F3F5F8", "#E2E6EC", "#1F2937", "#6B7280"
PAGE_W, PAGE_H, MARGIN, GAP, BAND_H = 1280, 720, 20, 12, 64
_vid = 0


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def color(hex_):
    return {"solid": {"color": lit(f"'{hex_}'")}}


def field(entity, prop, measure=False):
    return {"kind": "measure" if measure else "column", "entity": entity, "prop": prop}


NO_TOTALS = {"total": [{"properties": {"totals": lit("false")}}]}
DATA_LABELS = {"labels": [{"properties": {"show": lit("true")}}]}


def table_objects(widths: dict) -> dict:
    """No totals + fixed column widths (queryRef -> px) so a table fills its card instead of hugging the left."""
    return {**NO_TOTALS,
            "columnWidth": [{"properties": {"value": lit(f"{w}D")}, "selector": {"metadata": ref}} for ref, w in widths.items()]}

# Friendly headers for raw column names in tables and axes
DISPLAY_NAMES = {
    "dim_area.area": "Area", "fact_rent_yield.area": "Area", "fact_sales.project": "Project",
    "dim_property.rooms": "Bedrooms", "dim_property.segment": "Property type", "fact_sales.price_band": "Price band",
    "dim_date.month_name": "Month", "fact_sales.registration": "Registration",
    "fact_rent_yield.median_price_aed_m": "Median price (AED M)",
    "fact_rent_yield.median_annual_rent_aed_k": "Median rent (AED K/yr)",
    "fact_rent_yield.buildings": "Buildings",
    "fact_price_index.month": "Month", "fact_price_index.basket_areas": "Areas in basket",
    "fact_price_index.like_for_like_price_sqft": "Like-for-like AED/sq ft",
    "fact_price_index.price_index": "Like-for-like index",
    "fact_price_index.raw_avg_price_sqft": "Simple avg AED/sq ft",
    "fact_price_index.raw_index": "Simple avg index",
    "_Measures.Years of Rent to Buy": "Years to pay back", "_Measures.Area Rank by Sales": "Rank",
}


def container(x, y, w, h, single):
    global _vid
    _vid += 1
    cfg = {"name": f"v{_vid:03d}", "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": _vid * 1000, "width": w, "height": h}}],
           "singleVisual": single}
    return {"x": x, "y": y, "z": _vid * 1000, "width": w, "height": h, "config": json.dumps(cfg), "filters": "[]"}


def visual(vtype, x, y, w, h, roles: dict, title=None, order=None, objects=None):
    """roles: {role: [field, ...]}; order: (field, 'asc'|'desc')."""
    aliases, frm, select = {}, [], []
    for fields in roles.values():
        for f in fields:
            if f["entity"] not in aliases:
                aliases[f["entity"]] = f"t{len(aliases)}"
                frm.append({"Name": aliases[f["entity"]], "Entity": f["entity"], "Type": 0})

    def expr(f):
        key = "Measure" if f["kind"] == "measure" else "Column"
        return {key: {"Expression": {"SourceRef": {"Source": aliases[f["entity"]]}}, "Property": f["prop"]}}

    seen = []
    for fields in roles.values():
        for f in fields:
            ref = f"{f['entity']}.{f['prop']}"
            if ref not in seen:
                seen.append(ref)
                select.append({**expr(f), "Name": ref})
    query = {"Version": 2, "From": frm, "Select": select}
    if order:
        query["OrderBy"] = [{"Direction": 1 if order[1] == "asc" else 2, "Expression": expr(order[0])}]
    single = {
        "visualType": vtype,
        "projections": {role: [{"queryRef": f"{f['entity']}.{f['prop']}", **({"active": True} if i == 0 and role in ("Category", "Values") and vtype != "tableEx" else {})}
                               for i, f in enumerate(fields)] for role, fields in roles.items()},
        "prototypeQuery": query,
        "drillFilterOtherVisuals": True,
    }
    renames = {ref: {"displayName": DISPLAY_NAMES[ref]} for ref in seen if ref in DISPLAY_NAMES}
    if renames:
        single["columnProperties"] = renames
    if objects:
        single["objects"] = objects
    single["vcObjects"] = {"title": [{"properties": {"show": lit("true" if title else "false"),
                                                     **({"text": lit(f"'{title}'")} if title else {})}}]}
    return container(x, y, w, h, single)


def card(x, y, w, h, measure, label=None):
    """KPI card: big number + its label (the measure name unless `label` is given)."""
    v = visual("card", x, y, w, h, {"Values": [field(M, measure, True)]})
    if label:
        cfg = json.loads(v["config"])
        cfg["singleVisual"]["columnProperties"] = {f"{M}.{measure}": {"displayName": label}}
        v["config"] = json.dumps(cfg)
    return v


def text(x, y, w, h, runs, background=None, align="left"):
    """runs: list of paragraphs, each a list of (text, size_pt, color, bold)."""
    paragraphs = [{"textRuns": [{"value": t, "textStyle": {"fontSize": f"{s}pt", "color": c,
                                                           **({"fontWeight": "bold"} if b else {})}} for t, s, c, b in para],
                   **({"horizontalTextAlignment": align} if align != "left" else {})} for para in runs]
    single = {"visualType": "textbox", "drillFilterOtherVisuals": True,
              "objects": {"general": [{"properties": {"paragraphs": paragraphs}}]}}
    if background:
        single["vcObjects"] = {"background": [{"properties": {"show": lit("true"), "color": color(background), "transparency": lit("0D")}}],
                               "border": [{"properties": {"show": lit("false")}}],
                               "dropShadow": [{"properties": {"show": lit("false")}}]}
    else:
        single["vcObjects"] = {"background": [{"properties": {"show": lit("false")}}],
                               "border": [{"properties": {"show": lit("false")}}],
                               "dropShadow": [{"properties": {"show": lit("false")}}]}
    return container(x, y, w, h, single)


def header(title, subtitle):
    """Navy band across the top: page title + subtitle on the left, page navigator on the right."""
    band = text(0, 0, PAGE_W, BAND_H, [[(title, 17, "#FFFFFF", True)], [(subtitle, 9, "#C9D6E8", False)]], background=NAVY)
    nav = container(PAGE_W - MARGIN - 560, 14, 560, 36, {"visualType": "pageNavigator", "drillFilterOtherVisuals": True,
                                                       "vcObjects": {"background": [{"properties": {"show": lit("false")}}],
                                                                     "border": [{"properties": {"show": lit("false")}}],
                                                                     "dropShadow": [{"properties": {"show": lit("false")}}]}})
    return [band, nav]


def slicer(x, y, w, h, f, title):
    return visual("slicer", x, y, w, h, {"Values": [f]}, title=title,
                  objects={"data": [{"properties": {"mode": lit("'Dropdown'")}}],
                           "header": [{"properties": {"show": lit("false")}}]})


def columns(n, y, h, x0=MARGIN, width=PAGE_W - 2 * MARGIN):
    """Split a row into n equal boxes with GAP between them -> [(x, y, w, h), ...]."""
    w = (width - GAP * (n - 1)) / n
    return [(round(x0 + i * (w + GAP)), y, round(w), h) for i in range(n)]


M = "_Measures"
MONTH = field("dim_date", "month_name")
SEGMENT = field("dim_property", "segment")
OFFPLAN = field("fact_sales", "registration")
AREA = field("dim_area", "area")
NOTE_LINES = ["Source: Dubai Land Department Open Data", "Jan – Sep 2026 · Analysis by Nitheesha M V"]
SLICER_H = 56

ROW1 = BAND_H + 12                      # first content row (slicers or KPI cards)


def homes_filter() -> str:
    """Report-level filter: segment in (Apartment, Villa), editable in the Filters pane."""
    col = {"Column": {"Expression": {"SourceRef": {"Entity": "dim_property"}}, "Property": "segment"}}
    return json.dumps([{
        "name": "homesOnly",
        "expression": col,
        "filter": {
            "Version": 2,
            "From": [{"Name": "d", "Entity": "dim_property", "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": "segment"}}],
                "Values": [[{"Literal": {"Value": "'Apartment'"}}], [{"Literal": {"Value": "'Villa'"}}]],
            }}}],
        },
        "type": "Categorical",
        "howCreated": 1,
    }])


def filter_row(y, slicers):
    """Slicers on the left, source + filter note on the right."""
    boxes = columns(4, y, SLICER_H)
    v = [slicer(*boxes[i], f, t) for i, (f, t) in enumerate(slicers)]
    x, _, _, _ = boxes[len(slicers)]
    v.append(text(x, y, PAGE_W - MARGIN - x, SLICER_H, [[(line, 8, MUTED, False)] for line in NOTE_LINES], align="right"))
    return v


def page_overview():
    v = header("Dubai Property Market 2026",
               "Every DLD-registered home sale (apartments + villas), January – September 2026 · other types via the Filters pane")
    v += filter_row(ROW1, [(SEGMENT, "Property type"), (OFFPLAN, "Off-plan or ready"), (AREA, "Area")])
    cards_y = ROW1 + SLICER_H + GAP
    for box, (m, label) in zip(columns(5, cards_y, 84), [("Sales", "Home sales"), ("Sales Value (AED)", "Sales value (AED)"),
                                                         ("Avg Price per Sq Ft", "Avg price per sq ft (AED)"),
                                                         ("Off-plan Share %", "Off-plan share"),
                                                         ("Avg Deal (AED M)", "Avg deal size (AED M)")]):
        v.append(card(*box, m, label))
    top = cards_y + 84 + GAP
    h = (PAGE_H - MARGIN - top - GAP) // 2
    (a, b), (c, d) = columns(2, top, h), columns(2, top + h + GAP, h)
    v += [
        visual("clusteredColumnChart", *a, {"Category": [MONTH], "Y": [field(M, "Sales", True)]},
               title="Sales per month", order=(MONTH, "asc"), objects=DATA_LABELS),
        visual("lineChart", *b, {"Category": [MONTH], "Y": [field(M, "Avg Price per Sq Ft", True)]},
               title="Average price per sq ft (AED) — simple average", order=(MONTH, "asc"),
               objects={"lineStyles": [{"properties": {"showMarker": lit("true")}}]}),
        visual("columnChart", *c, {"Category": [MONTH], "Series": [OFFPLAN], "Y": [field(M, "Sales", True)]},
               title="Off-plan vs ready sales per month", order=(MONTH, "asc")),
        visual("clusteredBarChart", *d, {"Category": [field("dim_property", "rooms")], "Y": [field(M, "Sales", True)]},
               title="What people buy: sales by bedrooms", order=(field(M, "Sales", True), "desc"), objects=DATA_LABELS),
    ]
    return "Market overview", v


def page_index():
    v = header("Are prices really falling?", "Like-for-like apartment price index vs the simple average (January 2026 = 100)")
    for box, (m, label) in zip(columns(3, ROW1, 84), [("Like-for-like Change %", "Like-for-like price change, Jan → Sep"),
                                                      ("Simple Average Change %", "Simple average change, Jan → Sep"),
                                                      ("Mix Effect (index points)", "Explained by area mix (index points)")]):
        v.append(card(*box, m, label))
    note_y = ROW1 + 84 + GAP
    v.append(text(MARGIN, note_y, PAGE_W - 2 * MARGIN, 40,
                  [[("Why they differ: ", 10, INK, True),
                    ("the simple average falls when more sales happen in cheaper areas. The like-for-like index keeps the same "
                     "47 apartment areas with fixed weights, so it only moves when prices really change.", 10, MUTED, False)]],
                  background="#FFFFFF"))
    chart_y = note_y + 40 + GAP
    h = PAGE_H - MARGIN - chart_y
    table_w = 470                       # chart and table side by side: full-height chart, all 9 months visible
    chart_w = PAGE_W - 2 * MARGIN - table_w - GAP
    cols = ("month", "price_index", "raw_index", "like_for_like_price_sqft", "raw_avg_price_sqft")
    v += [visual("lineChart", MARGIN, chart_y, chart_w, h,
                 {"Category": [MONTH], "Y": [field(M, "Like-for-like Index", True), field(M, "Simple Average Index", True)]},
                 title="Apartment price index (January 2026 = 100)", order=(MONTH, "asc"),
                 objects={"lineStyles": [{"properties": {"showMarker": lit("true")}}]}),
          visual("tableEx", MARGIN + chart_w + GAP, chart_y, table_w, h,
                 {"Values": [field("fact_price_index", c) for c in cols]},
                 title="Monthly index values", order=(field("fact_price_index", "month"), "asc"),
                 objects=table_objects({f"fact_price_index.{c}": w for c, w in zip(cols, (80, 85, 85, 95, 95))}))]
    return "Price index", v


def page_areas():
    v = header("Areas: where the demand is", "Sales, value and price level by area — click an area to filter the value map")
    v += filter_row(ROW1, [(SEGMENT, "Property type"), (OFFPLAN, "Off-plan or ready")])
    top = ROW1 + SLICER_H + GAP
    h = PAGE_H - MARGIN - top
    table_w = 720
    v += [visual("tableEx", MARGIN, top, table_w, h,
                 {"Values": [AREA, field(M, "Sales", True), field(M, "Value (AED bn)", True), field(M, "Avg Price per Sq Ft", True),
                             field(M, "Off-plan Share %", True), field(M, "Area Rank by Sales", True)]},
                 title="Area leaderboard", order=(field(M, "Sales", True), "desc"),
                 objects=table_objects({"dim_area.area": 205, f"{M}.Sales": 80, f"{M}.Value (AED bn)": 95,
                                        f"{M}.Avg Price per Sq Ft": 105, f"{M}.Off-plan Share %": 95, f"{M}.Area Rank by Sales": 55})),
          visual("scatterChart", MARGIN + table_w + GAP, top, PAGE_W - 2 * MARGIN - table_w - GAP, h,
                 {"Category": [AREA], "X": [field(M, "Sales", True)], "Y": [field(M, "Avg Price per Sq Ft", True)]},
                 title="Value map: sales (across) vs price per sq ft (up)")]
    return "Areas", v


def page_buyers():
    v = header("Buyers and projects", "What sells, at what price, and which projects lead")
    for box, (m, label) in zip(columns(3, ROW1, 84), [("Median Price (AED M)", "Median home price (AED M)"),
                                                      ("Share Under AED 2M", "Homes sold under AED 2M"),
                                                      ("Studios & 1-Beds Share", "Studios and 1-bedrooms")]):
        v.append(card(*box, m, label))
    top = ROW1 + 84 + GAP
    chart_h = 236
    (a, b) = columns(2, top, chart_h)
    v += [visual("clusteredColumnChart", *a, {"Category": [field("fact_sales", "price_band")], "Y": [field(M, "Sales", True)]},
                 title="Sales by price band (AED)", order=(field("fact_sales", "price_band"), "asc"), objects=DATA_LABELS),
          visual("clusteredBarChart", *b, {"Category": [SEGMENT], "Y": [field(M, "Sales", True)]},
                 title="Sales by property type", order=(field(M, "Sales", True), "desc"), objects=DATA_LABELS),
          visual("tableEx", MARGIN, top + chart_h + GAP, PAGE_W - 2 * MARGIN, PAGE_H - MARGIN - (top + chart_h + GAP),
                 {"Values": [field("fact_sales", "project"), AREA, field(M, "Sales", True), field(M, "Value (AED bn)", True),
                             field(M, "Avg Price per Sq Ft", True), field(M, "Off-plan Share %", True)]},
                 title="Projects by sales value", order=(field(M, "Value (AED bn)", True), "desc"),
                 objects=table_objects({"fact_sales.project": 330, "dim_area.area": 260, f"{M}.Sales": 120, f"{M}.Value (AED bn)": 150,
                                        f"{M}.Avg Price per Sq Ft": 170, f"{M}.Off-plan Share %": 150}))]
    return "Buyers & projects", v


def page_yield():
    ry = "fact_rent_yield"
    v = header("Where do apartments pay back fastest?",
               "Gross rental yield: 34,649 new leases (Sep 2026) vs ready-apartment prices in the same buildings")
    for box, (m, label) in zip(columns(3, ROW1, 84), [("Median Gross Yield", "Median gross yield (35 areas)"),
                                                      ("Best Gross Yield", "Highest yield (Dubai Investment Park 2)"),
                                                      ("Areas Measured", "Areas with 3+ matched buildings")]):
        v.append(card(*box, m, label))
    top = ROW1 + 84 + GAP
    h = PAGE_H - MARGIN - top
    bar_w = 540
    v += [visual("clusteredBarChart", MARGIN, top, bar_w, h, {"Category": [field(ry, "area")], "Y": [field(M, "Gross Yield %", True)]},
                 title="Gross rental yield by area", order=(field(M, "Gross Yield %", True), "desc"), objects=DATA_LABELS),
          visual("tableEx", MARGIN + bar_w + GAP, top, PAGE_W - 2 * MARGIN - bar_w - GAP, h,
                 {"Values": [field(ry, "area"), field(M, "Gross Yield %", True), field(M, "Years of Rent to Buy", True),
                             field(ry, "median_price_aed_m"), field(ry, "median_annual_rent_aed_k"), field(ry, "buildings")]},
                 title="Yield table", order=(field(M, "Gross Yield %", True), "desc"),
                 objects=table_objects({"fact_rent_yield.area": 200, f"{M}.Gross Yield %": 75, f"{M}.Years of Rent to Buy": 85,
                                        "fact_rent_yield.median_price_aed_m": 100, "fact_rent_yield.median_annual_rent_aed_k": 110,
                                        "fact_rent_yield.buildings": 75}))]
    return "Rental yield", v


def solid(c):
    return {"solid": {"color": c}}


THEME = {
    "name": "Dubai Property 2026 — Navy",
    "dataColors": [BLUE, ORANGE, "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
    "foreground": INK, "foregroundNeutralSecondary": MUTED, "foregroundNeutralTertiary": "#9CA3AF",
    "background": "#FFFFFF", "backgroundLight": CANVAS, "backgroundNeutral": CARD_BORDER,
    "tableAccent": NAVY, "good": "#0ca30c", "neutral": "#eda100", "bad": "#d03b3b",
    "textClasses": {
        "callout": {"fontSize": 24, "fontFace": "Segoe UI Semibold", "color": NAVY},
        "title": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": INK},
        "header": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": INK},
        "label": {"fontSize": 9, "fontFace": "Segoe UI", "color": MUTED},
    },
    "visualStyles": {
        "*": {"*": {
            "background": [{"show": True, "color": solid("#FFFFFF"), "transparency": 0}],
            "border": [{"show": True, "color": solid(CARD_BORDER), "radius": 10}],
            "dropShadow": [{"show": True, "color": solid("#0F172A"), "position": "Outer", "preset": "Custom",
                            "shadowSpread": 0, "shadowBlur": 8, "angle": 90, "shadowDistance": 2, "transparency": 92}],
            "title": [{"show": True, "fontColor": solid(INK), "fontSize": 11, "fontFamily": "Segoe UI Semibold"}],
            "padding": [{"top": 8, "bottom": 8, "left": 12, "right": 12}],
            "categoryAxis": [{"showAxisTitle": False, "labelColor": solid(MUTED), "fontSize": 9}],
            "valueAxis": [{"showAxisTitle": False, "labelColor": solid("#9CA3AF"), "fontSize": 8,
                           "gridlineShow": True, "gridlineColor": solid("#EDF0F4"), "gridlineStyle": "solid"}],
            "legend": [{"show": True, "position": "TopRight", "fontSize": 9, "labelColor": solid(MUTED)}],
            "labels": [{"color": solid("#374151"), "fontSize": 8}],
        }},
        "page": {"*": {"background": [{"color": solid(CANVAS), "transparency": 0}],
                       "outspace": [{"color": solid("#E9EDF2"), "transparency": 0}]}},
        "card": {"*": {"labels": [{"color": solid(NAVY), "fontSize": 24, "fontFamily": "Segoe UI Semibold"}],
                       "categoryLabels": [{"show": True, "color": solid(MUTED), "fontSize": 9}],
                       "title": [{"show": False}]}},
        "tableEx": {"*": {"columnHeaders": [{"fontColor": solid("#FFFFFF"), "backColor": solid(NAVY), "fontFamily": "Segoe UI Semibold",
                                             "fontSize": 9, "alignment": "Left", "wordWrap": True}],
                          "values": [{"fontColorPrimary": solid(INK), "backColorPrimary": solid("#FFFFFF"),
                                      "fontColorSecondary": solid(INK), "backColorSecondary": solid("#F6F8FB"), "fontSize": 9}],
                          "grid": [{"gridHorizontal": True, "gridHorizontalColor": solid("#EDF0F4"), "gridVertical": False,
                                    "rowPadding": 5, "outlineColor": solid(CARD_BORDER)}]}},
        "slicer": {"*": {"header": [{"show": False}],
                         "items": [{"fontColor": solid(INK), "fontSize": 10}],
                         "title": [{"show": True, "fontSize": 8, "fontColor": solid(MUTED), "fontFamily": "Segoe UI"}],
                         "padding": [{"top": 4, "bottom": 4, "left": 10, "right": 10}]}},
        "pageNavigator": {"*": {
            "fill": [{"$id": "default", "show": True, "fillColor": solid("#1E4677"), "transparency": 0},
                     {"$id": "hover", "fillColor": solid("#2A5A92")},
                     {"$id": "selected", "fillColor": solid("#FFFFFF")}],
            "text": [{"$id": "default", "show": True, "fontColor": solid("#FFFFFF"), "fontSize": 9, "fontFamily": "Segoe UI Semibold"},
                     {"$id": "selected", "fontColor": solid(NAVY)}],
            "outline": [{"$id": "default", "show": False}],
            "shape": [{"$id": "default", "tileShape": "rectangleRounded", "roundEdge": 6}],
            "background": [{"show": False}], "border": [{"show": False}], "dropShadow": [{"show": False}],
        }},
        "textbox": {"*": {"background": [{"show": False}], "border": [{"show": False}], "dropShadow": [{"show": False}]}},
    },
}


def build_report() -> dict:
    sections = []
    for i, builder in enumerate((page_overview, page_index, page_areas, page_buyers, page_yield)):
        name, visuals = builder()
        sections.append({"name": f"Section{i + 1}", "displayName": name, "displayOption": 1, "width": PAGE_W, "height": PAGE_H,
                         "config": "{}", "filters": "[]", "visualContainers": visuals, "ordinal": i})
    config = {"version": "5.59", "themeCollection": {"customTheme": {"name": "DubaiTheme.json", "version": "5.59", "type": 1}},
              "activeSectionIndex": 0, "linguisticSchemaSyncVersion": 0,
              "objects": {"outspacePane": [{"properties": {"expanded": lit("true")}}]}}
    return {"config": json.dumps(config), "layoutOptimization": 0, "filters": homes_filter(),
            "resourcePackages": [{"resourcePackage": {"name": "RegisteredResources", "type": 1, "disabled": False,
                                                      "items": [{"type": 202, "path": "DubaiTheme.json", "name": "DubaiTheme.json"}]}}],
            "sections": sections}


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) if not isinstance(obj, str) else obj, encoding="utf-8")


def main() -> None:
    # Files are overwritten in place: deleting the folders fails while OneDrive or Power BI holds them,
    # and Power BI's own .pbi/ cache folder inside them is kept.
    write(POWERBI_DIR / f"{NAME}.pbip", {"version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
                                         "settings": {"enableAutoRecovery": True}})
    write(SM / "definition.pbism", {"version": "1.0", "settings": {}})
    write(SM / "model.bim", build_model())
    write(RP / "definition.pbir", {"version": "1.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}, "byConnection": None}})
    write(RP / "report.json", build_report())
    write(RP / "StaticResources" / "RegisteredResources" / "DubaiTheme.json", THEME)
    print(f"wrote {POWERBI_DIR / (NAME + '.pbip')} ({len(MEASURES)} measures, {len(RELATIONSHIPS)} relationships, 5 pages)")


if __name__ == "__main__":
    main()
