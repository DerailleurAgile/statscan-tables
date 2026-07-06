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

## Add New Entries Below

Format:
```
## [Series description] (Table [PID])

| Series | Vector | Notes |
|---|---|---|
| ... | v... | ... |

Any view/cube mismatches, SA/NSA gotchas, or conflation pairs discovered.
```
