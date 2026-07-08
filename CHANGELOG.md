# Changelog

The skill's version lives in SKILL.md frontmatter (`version:`). Bump it and add an entry here
with every change that gets packaged/uploaded — patch for fixes, minor for behavior changes.

## 1.2.0 — 2026-07-08

Alignment with statscan-to-pbc (the non-PBC lessons from its known-vectors ledger and its
`--aggregate` re-timescaling feature — no chart/XmR/PBC Analyzer PRO material):

- `wds_fetch.py`: `--aggregate monthly|bimonthly|quarterly|annual` + `--agg-method mean|sum`
  re-timescales a series before any transform (e.g. weekly source to monthly, monthly to
  quarterly/annual); incomplete edge buckets are dropped; YoY runs on the aggregated series so
  annual YoY is the change in annual averages (StatsCan's own method); header provenance switches
  to "Compiled from Table". `clean_points` now keeps day-level dates for true sub-monthly sources
  (month-start refPers still collapse to `YYYY-MM` as before) so `--aggregate` can bucket them.
- `to_yoy` renamed `yoy_series` and generalized to diff any label sharing a year prefix
  (`YYYY`, `YYYY-MM`, `YYYY-Qn`), not just `YYYY-MM` — needed for `--aggregate`'s quarterly/annual
  output, same percentage-point rounding as before.
- Step 5 header guidance: don't default every series to "YoY Inflation" — only correct for
  CPI-family index series differenced month-over-month.
- known-vectors: four new entries — Job Vacancy Rate (14-10-0372, replaces the archived monthly
  tables), Business Sector Labour Productivity (36-10-0206), New Housing Price Index (18-10-0205),
  public/private sector employees (14-10-0026, thousands scalar-factor trap + summer-student
  seasonal pattern) — plus an out-of-scope list for series that aren't in WDS at all (OSB
  insolvencies, CMHC housing starts).

## 1.1.0 — 2026-07-07

Alignment with statscan-to-pbc v1.1.0 (the non-PBC lessons from its claude.ai/cloud shakedown):

- Cloud-session note in Step 2: `www150.statcan.gc.ca` must be in the environment's custom
  network allowlist or all WDS calls fail; clipboard copy is silently skipped in cloud sessions.
- Output files go to the session temp/scratchpad directory by default, into the project only on
  request.
- `version:` in SKILL.md frontmatter; this changelog; `dist/` zip packaging for claude.ai upload.

(The frontmatter description was already within claude.ai's 1024-character upload limit, and
tab-delimited output was already the default here — no changes needed for those.)

## 1.0.0 — 2026-07-06

- Initial packaged skill: WDS fetch/verify pipeline (stdlib-only scripts), cached cube metadata,
  known-vectors reference, clipboard auto-copy.
