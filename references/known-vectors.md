# Known Vectors and Traps — StatsCan Tables

Verified in use. Add to this file whenever a new vector is confirmed correct, so future
fetches skip the discovery step and inherit the trap-avoidance already worked out.

---

## CPI Food (Table 18-10-0004 family)

| Series | Vector | Notes |
|---|---|---|
| Food, Canada, NSA index | **v41690974** | Use this for food YoY inflation. 2002=100. |
| Food purchased from stores, Canada, NSA | v41690975 | The Daily's headline "grocery" number — narrower than total Food. Don't conflate. |
| All-items, Canada, NSA | v41690973 | For comparison against food. |
| Food, Canada, seasonally adjusted | v41690915 | Wrong choice for YoY — YoY differencing already handles seasonality; SA is for month-over-month comparisons instead. |

**18-10-0004-03 is a view**, not the cube itself. The underlying PID is **18100004**. The view
displays percentage changes on screen; the API only serves the index values behind them. Year-over-
year figures must be computed: `(index_t / index_t−12 − 1) × 100`.

**Known distortion in this series:** the GST/HST holiday (Dec 14, 2024 – Feb 15, 2025) suppressed
food-adjacent prices — mostly restaurant and prepared food, since basic groceries were already
GST zero-rated — then its expiry created base-effect distortion in YoY comparisons roughly twelve
months later (Dec 2025–Feb 2026, strongest in January). A spike or dip in either window has a
documented, findable explanation — useful to know before treating it as news. Total Food is
affected much more than Food purchased from stores.

---

## Emigration components (Table 17-10-0040)

| Series | Vector | Notes |
|---|---|---|
| Emigrants, Canada | v29850343 | Gross permanent outflow. The plain reading of "emigration figures". |
| Net emigration, Canada | v1566834788 | Emigrants − returning emigrants + net temporary emigration. Different story from gross — don't conflate. |

**Quarterly, not monthly** — there is no monthly emigration series; requests for "monthly" figures
mean this quarterly cube. Annual figures must be compiled by summing four calendar quarters
(provenance: "Compiled from Table 17-10-0040"); exclude years with fewer than 4 quarters published
(the current year is always partial until the Q4 release).

**Known distortion:** 2020 COVID travel restrictions collapsed emigration (net emigration ~19K vs.
a ~50K norm) — a documented explanation, not a data error.

---

## Labour Force Survey (Table 14-10-0287)

| Series | Vector | Notes |
|---|---|---|
| Unemployment rate, Ontario, 15+, total gender, SA | v2063949 | The headline monthly rate. Coordinate 7.7.1.1.1.1 (Geo.Characteristic.Gender.Age.Statistic.DataType). |

**Use the seasonally adjusted series** for month-to-month comparisons — the unadjusted series
(data type member 2) shows the seasonal cycle, not the underlying trend. Statistics dimension:
member 1 = Estimate; member 2 is the standard error, easy to grab by accident. Values are already
in percent units (7.0 = 7.0%).

**Title trap:** this cube's `SeriesTitleEn` has six `;`-segments and the *last* one is the
adjustment type, so a keep-last-segment title strip yields "Seasonally Adjusted" instead of
"Unemployment rate". Override the title manually for headers from this table.

---

## Job Vacancy Rate (Table 14-10-0372)

| Series | Vector | Notes |
|---|---|---|
| Job vacancy rate, Canada, total all industries, monthly, NSA | v1212389467 | Coordinate 1.1.4.0.0.0.0.0.0.0 (Geo.Industry.Statistic). Percent units already. Monthly, unadjusted — no SA version exists at this cadence (SA is only in the quarterly JVWS tables), so expect seasonal cycling. |

**Note:** this table replaced the older monthly job vacancy tables archived Sept 2025; if search
results surface 14-10-0325/0326/0328/0356, those are dead — use 14-10-0372 (or its 1410044x
siblings) instead.

---

## Business Sector Labour Productivity (Table 36-10-0206)

| Series | Vector | Notes |
|---|---|---|
| Labour productivity, Canada, business sector, quarterly, SA index | v1409153 | Coordinate 1.1.1.0.0.0.0.0.0.0. This is the cube itself (no view trap). Index, 2017=100, already seasonally adjusted. Quarterly cadence — only ~4 points/year, so a multi-year window is needed before drawing any conclusion about trend vs. noise. |

**Known context:** productivity had a multi-year soft patch (declines most of 2022–2024) with a
tentative recovery starting Q4 2024 — worth knowing before treating a recent uptick as news.

---

## New Housing Price Index (Table 18-10-0205)

| Series | Vector | Notes |
|---|---|---|
| NHPI, Canada, total (house and land), monthly, NSA | v111955442 | Coordinate 1.1.0.0.0.0.0.0.0.0. Index, December 2016=100. This table is already the cube — no separate view/percent-change trap, unlike CPI. |

**Conflation trap:** dimension 2 also has "House only" and "Land only" — don't grab those by
accident if the user wants the headline "new home prices" number, which is Total (house and land).

---

## Out of Scope — Not in StatsCan WDS

Some commonly-requested "StatsCan-adjacent" series are actually published by other agencies and
won't turn up via `cube_metadata.py` or the WDS endpoints no matter how the search terms are varied.
Confirm the actual source before spending time on cube/vector discovery:

| Series | Actual source | Notes |
|---|---|---|
| Business/personal insolvencies, bankruptcies | Office of the Superintendent of Bankruptcy (OSB), an independent federal office — not StatsCan | Published separately from StatsCan's WDS; would need its own fetch approach (OSB's site, not `getDataFromVectorsAndLatestNPeriods`). |
| Housing starts | Canada Mortgage and Housing Corporation (CMHC) | CMHC publishes an all-up Excel workbook (multiple sheets) on its downloads page rather than a WDS-queryable vector. Would need an Excel-parsing approach, not the WDS fetch flow this skill wraps. |

If a request calls for either of these, the shape of the work is different from Steps 1–4 here (no
vector, no `getCubeMetadata`) — it's a spreadsheet-ingestion task, outside what this skill covers.

---

## Employment by Class of Worker — Public vs. Private Sector (Table 14-10-0026)

| Series | Vector | Notes |
|---|---|---|
| Public sector employees, Canada, all industries, total gender, monthly NSA | v3437443 | Coordinate 1.3.1.1.0.0.0.0.0.0. **`scalarFactorCode` is 3 (thousands)** — a value like 4571.3 means 4,571,300 people, not 4,571. Watch this one; it's exactly the "unexpected scalar factor" trap Step 3 warns about. |
| Private sector employees, Canada, all industries, total gender, monthly NSA | v3437444 | Coordinate 1.4.1.1.0.0.0.0.0.0. Same thousands scaling as above. |

**Conflation note:** this is a genuine sector-of-employer split (class of worker), unlike the Job
Vacancy Rate table's NAICS "Public administration" category, which only captures core government
administration and misses public-sector workers embedded in health care, education, and utilities.
Don't substitute one for the other — they answer different questions ("is the public sector
employing more/fewer people" vs. "are government-administration positions specifically hard to
fill").

There's also a seasonally-adjusted monthly companion table (14-10-0028) with the same Class of
Worker dimension, if SA behavior is preferred over NSA.

**Known seasonal pattern (private sector share of total employees):** a strong, recurring
July-August peak every year, driven by the student summer job market — the LFS runs a dedicated
May-August "returning students" supplement, and StatsCan's own releases confirm private-sector
employee counts swell each summer (concentrated in retail trade and accommodation/food services)
while public-sector counts don't follow the same rhythm (schools wind down rather than ramping up).
This is a stable, repeating composition effect, not a change in the underlying trend — expect it
every year rather than treating it as new.

---

## Add New Entries Below

Format:
```
## [Series description] (Table [PID])

| Series | Vector | Notes |
|---|---|---|
| ... | v... | ... |

Any view/cube mismatches, SA/NSA gotchas, or conflation pairs discovered.
```
