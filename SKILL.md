---
name: statscan-tables
version: 1.1.0
description: >
  Activate this skill whenever the user wants to fetch, download, or update a Statistics Canada
  time series. Trigger on mentions of "StatsCan", "Statistics Canada", a table number in the
  NN-NN-NNNN(-NN) format, a CANSIM/WDS vector (vNNNNNNNN), or requests like "pull the latest food
  inflation numbers," "update the housing starts series," or "get me a clean CSV of the
  unemployment rate." Also trigger for recurring release-day rituals (CPI day, Labour Force Survey
  day, housing starts day) where the user wants a clean, verified, chronologically-ordered
  two-column series without having to navigate StatsCan's table UI by hand. This skill governs how
  to use the Web Data Service (WDS) correctly — including known traps around views vs. cubes, NSA
  vs. SA series, YoY transformations, and vector conflation — not general StatsCan browsing or
  one-off manual CSV downloads that don't need verification rigor.
---

# StatsCan Tables

You are fetching data from Statistics Canada's Web Data Service (WDS) and preparing it as a clean,
verified, chronologically-ordered two-column series (Date, Value) ready for whatever the user is
doing next — a spreadsheet, a chart, a dashboard, an analysis. Your job is not just to fetch; it's
to fetch *correctly*, catch the traps that produce a wrong-but-plausible-looking series, and make
verification easy for the user.

The scripts in `scripts/` use only the Python standard library — no installs needed beyond
Python 3.10+.

---

## Core Principle: Views Are Not Cubes

A StatsCan "table number" like 18-10-0004-**03** is often a *display view* of an underlying cube.
The view number after the second hyphen is not part of the product ID (PID) the API uses.

- The PID is the table number **without hyphens and without the trailing view suffix**:
  18-10-0004-03 → PID **18100004**.
- Views frequently show *derived* figures (percentage changes, ratios) that don't exist as their
  own series in the API. The API serves the underlying **index or level values**. If the user wants
  a percentage change (especially year-over-year), you almost always need to fetch the index and
  **compute the transformation yourself** — state the formula explicitly before you use it.

Do not assume a view's displayed column maps to a vector 1:1. Confirm what's actually being served.

---

## Step 1: Identify the Vector

**If the user gives you a vector ID directly** (e.g., "fetch v41690974"), skip to Step 2.

**If the user gives you a table number and a plain-language series description:**

1. Inspect the cube's dimensions and members with the cached metadata tool — don't call the API
   ad hoc:
   ```
   python scripts/cube_metadata.py 18100004 [--grep keyword] [--all] [--refresh]
   ```
   It caches `getCubeMetadata` responses for 30 days under
   `%LOCALAPPDATA%/statscan-tables/cube-cache` (`~/.cache/statscan-tables` elsewhere), so repeat
   discovery on a cube costs nothing. Use `--refresh` if a cube's structure seems stale (new
   geography, renamed member); the cache is safe to delete wholesale. The raw endpoint, should you
   need it directly: `POST .../getCubeMetadata` with body `[{"productId": 18100004}]`.
2. Match the user's plain-language description to specific dimension members (geography, product
   group, adjustment type, etc.). **Show your matched members to the user before proceeding** —
   this is the single biggest place a wrong series gets fetched while looking fine. A mismatched
   dimension member (wrong geography, wrong sub-aggregate) produces a series that charts perfectly
   well and is simply not the thing anyone asked for.
3. Confirm the vector with `getSeriesInfoFromCubePidCoord` using the coordinate you built.

**If you already know the common series** (see `references/known-vectors.md` for a running list of
vectors this project has verified — CPI food, all-items, unemployment rate, etc.), use the verified
vector directly, but still state which one and why, since verified vectors can still be
conflated with a similarly-named sibling (see the trap below).

### The conflation trap
Headline coverage and the series the user actually wants are frequently *not the same series*.
Classic case: "food inflation" could mean **Food** (all food, including restaurants) or **Food
purchased from stores** (retail only, usually the one the Daily headlines). These have different
vectors and different values. When a plain-language request is ambiguous this way, ask, or fetch
both and let the user pick — don't silently guess.

---

## Step 2: Fetch

```
POST https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVectorsAndLatestNPeriods
Body: [{"vectorId": <integer, no "v" prefix>, "latestN": <count>}]
```

- `vectorId` is a bare integer. `"v41690974"` will fail; `41690974` will not.
- **If the destination transformation needs trailing history** (e.g., year-over-year needs 12
  prior months per output point), fetch `latestN` = desired output months + 12, and say so.
- Multiple vectors can be fetched in one call by adding more objects to the array — useful for
  comparison series (e.g., food vs. all-items).
- **Cloud/web sessions (claude.ai/code):** the default Trusted network allowlist does not include
  StatsCan, so all WDS calls fail. The environment needs Network access set to **Custom** with
  `www150.statcan.gc.ca` in Allowed domains (the scripts are stdlib-only, so no package-registry
  access is required). If a fetch fails with a proxy/connection error in a cloud session, report
  this cause and fix to the user — don't retry or hunt for other bugs. Clipboard copy is silently
  skipped there; hand over the file and/or inline data instead.

For the common cases, `scripts/wds_fetch.py` does Steps 2–5 in one run:

```
python scripts/wds_fetch.py [vectorId] [months] [--transform yoy|raw] [--out FILE]
```

It fetches, cleans, transforms (YoY computed from the index, +12 months of trailing history
handled automatically), writes a tab-delimited two-column file with a provenance-bearing header,
and prints the Step 4 verification block.

---

## Step 3: Clean and Transform

For each returned datapoint:

- **Skip non-value status codes.** `statusCode` other than a normal value (StatsCan uses codes for
  "not available" and similar) means there's no real number for that period — drop it, don't
  interpolate or invent one.
- **Check `scalarFactorCode`.** For CPI-type series this is normally 0 (units, no scaling needed).
  If it isn't 0 for a series you expected to be a plain index, stop and flag it — silently applying
  or ignoring an unexpected scalar factor is exactly the kind of "worked on the wrong assumption"
  error that data verification exists to prevent.
- **Sort chronologically, oldest first.** An unsorted time series is silently wrong in a way that
  won't show up until someone reads the x-axis carefully.
- **Apply the stated transformation explicitly.** For year-over-year: `(value_t / value_t−12 − 1)
  × 100`, matched to the same calendar month a year prior — not simply the 12th-prior row, in case
  of gaps. Round to the precision StatsCan itself publishes (CPI YoY is typically 1 decimal) so the
  verification step in Step 4 is a clean match, not an approximation debate.
- **Note preliminary/revised flags** (`symbolCode` on the datapoint) if present — a value still
  marked preliminary deserves a second look after the next release, and it's worth telling the
  user this rather than presenting the point with false confidence.

---

## Step 4: Verify Before Handing Off

Never hand back a CSV without first showing:

1. **The exact series title(s) fetched** — as returned by the API, not your paraphrase of the request.
2. **The reference period range** — first and last period in the output.
3. **The last 2–3 computed values**, so the user can spot-check against the StatsCan table page or
   the most recent Daily release in about fifteen seconds.

If a StatsCan published figure is available for comparison (e.g., a headline YoY % from The Daily),
say so explicitly and note whether your computed value matches. A mismatch almost always traces
back to a conflated series (Step 1) or a transformation mismatch (Step 3) — flag which is more
likely rather than just reporting the discrepancy.

---

## Step 5: Output Format

Default output: a two-column series, no extra columns, no metadata rows, no footnotes.
`scripts/wds_fetch.py` writes it tab-delimited for painless spreadsheet pasting.

```
Date	Value
2024-01	3.9
2024-02	3.7
...
```

- `Date` in `YYYY-MM` for monthly series.
- `wds_fetch.py` also copies the result to the clipboard automatically (pass `--no-clip` to skip,
  e.g. in scheduled jobs) — tell the user it's ready to paste into Excel or a text file.
- Ask the user if they want the file, the data pasted inline in the response, or both — inline is
  frequently more convenient than a file the user has to open and re-copy from.
- Write the file to the session's temp/scratchpad directory, not the user's project or working
  directory — a data pull is usually paste-and-go, and strays shouldn't litter the repo. Save it
  into the project only when the user asks to keep it.

### Building the Value column header

A plain `Value` header loses everything about how the number was derived — once a sheet is passed
along, nobody downstream can tell a raw index from a YoY % from a compiled annual sum just by
looking. Build the header instead of hardcoding it, from four parts:

```
StatsCan: <transform> <series title> (<start>-<end>) — <provenance>: <table>
```

- **`<series title>`** — from the vector's own metadata (`SeriesTitleEn` via
  `getSeriesInfoFromVector`), not your paraphrase. Strip the leading `Canada;`-style geography
  prefix if the geography is already obvious from context. Watch the multi-dimension title trap
  in `references/known-vectors.md` — for some cubes the last title segment is the adjustment
  type, not the series name.
- **`<transform>`** — state what was actually done, not a fixed assumption: `"Raw Index"`, `"YoY %
  Change"`, `"May vs. Prior May % Change"` (or whatever the comparison cadence actually is),
  `"Estimated Annual"` (for a quarterly/monthly series compiled into annual totals), etc.
- **`(<start>-<end>)`** — compute this from the actual output data's first and last period, never
  type it by hand. A hand-typed range is exactly the kind of thing that silently drifts or typos
  (`2010-206` instead of `2010-2025`) when the window changes on a later run.
- **`<provenance>`** — `Table: NN-NN-NNNN` for a straight pull of the table's own series; `Compiled
  from Table: NN-NN-NNNN` whenever you aggregated (summed quarters into years, filtered to one
  month per year, etc.) — the wording should tell an auditor whether the number came out of the
  table as-is or was built from it.
- Table code is the PID reformatted with hyphens: `NN-NN-NNNN` (e.g. productId `18100004` →
  `18-10-0004`).

---

## Recurring / Release-Day Use

If the user wants this run repeatedly (e.g., "update this every month after CPI day"), treat it as
a standing ritual rather than a one-off: reuse the same verified vector(s), same transformation,
same window length, and always re-run the Step 4 verification even though it worked last time —
StatsCan revises data, and a routine has to survive the month that method breaks quietly.

---

## Known Traps Reference

For a running list of verified vectors, common conflation pairs, and dimension quirks discovered
in use (NSA vs. SA, view-vs-cube mismatches, etc.), see `references/known-vectors.md`.
Add newly verified vectors there as they come up, so future fetches don't repeat the discovery work.
