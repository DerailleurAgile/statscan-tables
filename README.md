# statscan-tables

A [Claude Code](https://claude.com/claude-code) agent skill for fetching Statistics Canada time
series from the Web Data Service (WDS) — correctly. **Python standard library only; nothing to
install beyond Python 3.10+.**

Fetching StatsCan data is full of traps that produce wrong-but-plausible series: table "views"
that aren't the underlying cube, conflated sibling series ("Food" vs. "Food purchased from
stores"), seasonally-adjusted vs. unadjusted choices, year-over-year figures the API doesn't
actually serve, and standard-error members sitting one id away from the estimates. This skill
encodes the protocol for dodging all of them, and always hands back a verification block (exact
series title from the API, period range, last few values) so results can be spot-checked against
The Daily in seconds.

## Install

**As a Claude Code skill** — download the ZIP (green "Code" button → Download ZIP, or
[this link](https://github.com/DerailleurAgile/statscan-tables/archive/refs/heads/main.zip)) and
extract it into your skills directory so it looks like:

```
~/.claude/skills/statscan-tables/
├── SKILL.md
├── references/
└── scripts/
```

(Or `git clone https://github.com/DerailleurAgile/statscan-tables ~/.claude/skills/statscan-tables`.)
Then ask Claude things like *"pull the last 24 months of food inflation as YoY %"* or type
`/statscan-tables`. For a single project instead, put the folder under `<project>/.claude/skills/`.

## What's in the box

- **`SKILL.md`** — the fetch → clean → transform → verify protocol Claude follows, including the
  views-vs-cubes rule, the conflation trap, and provenance-bearing column headers.
- **`scripts/wds_fetch.py`** — fetch a vector, emit a clean tab-delimited Date/Value file
  (raw values or YoY % change computed from the index, with optional `--aggregate` re-timescaling
  to bimonthly/quarterly/annual first), print the verification block, and **copy the result to
  the clipboard automatically** so it pastes straight into Excel, Google Sheets, or a text file
  (`--no-clip` to disable, e.g. for scheduled jobs).
- **`scripts/cube_metadata.py`** — cube discovery with a 30-day disk cache: dimensions and
  members, filterable, so matching a plain-language request to a vector coordinate is one command.
- **`references/known-vectors.md`** — a starter ledger of verified vectors and documented traps
  (CPI food family, emigration components, LFS unemployment). The skill appends to it as new
  series are verified — it's why the second fetch of any series is instant.

## Examples

### Asking Claude

> **"Pull the last 12 months of grocery inflation as YoY %."**

Claude resolves the series from the ledger (and because "grocery" vs. "food" is a known conflation
pair, tells you which it picked — or asks), runs the fetch, and replies with the verification
block plus the data:

```
Series:  YoY % Change Food Purchased From Stores (Table 18-10-0004, v41690975)
Range:   2025-06 to 2026-05
Last 3:  2026-03: 4.4, 2026-04: 3.8, 2026-05: 4.3
Copied to clipboard — paste straight into Excel, Sheets, or a text file.
```

> **"Get me Ontario's monthly unemployment rate for the past 3 years."**

For a series not yet in the ledger, Claude first shows you the dimension members it matched
(geography, age group, seasonal adjustment...) before fetching — the step that catches
wrong-but-plausible series — then adds the verified vector to the ledger so next time is instant.

### Direct script use (no Claude required)

```
$ python scripts/wds_fetch.py 41690975 12
Wrote 12 rows to statscan_series.csv
Copied to clipboard — paste straight into Excel, Sheets, or a text file.
Series:  YoY % Change Food Purchased From Stores (Table 18-10-0004, v41690975)
Range:   2025-06 to 2026-05
Last 3:  2026-03: 4.4, 2026-04: 3.8, 2026-05: 4.3
```

The file (and your clipboard) now hold a tab-delimited series whose header records exactly how the
numbers were derived:

```
Date	StatsCan: YoY % Change Food Purchased From Stores (2025-06-2026-05) — Table: 18-10-0004
2025-06	2.8
2025-07	3.4
2025-08	3.5
...
2026-05	4.3
```

Raw index values instead of YoY: add `--transform raw`. Keep your clipboard untouched: `--no-clip`.

### Discovering what's in a table

```
$ python scripts/cube_metadata.py 18100004 --grep "food purchased"
[cache] ...\statscan-tables\cube-cache\18100004.json (0 days old)
Title: Consumer Price Index, monthly, not seasonally adjusted
Range: 1914-01-01 to 2026-05-01  (frequency code 6)

DIM 2: Products and product groups (359 members)
   4  Food purchased from stores
   75  Food purchased from restaurants
   ...
```

First call hits the network; repeats are served from a 30-day disk cache.

## License

MIT — use it freely. Statistics Canada data is subject to the
[Statistics Canada Open Licence](https://www.statcan.gc.ca/en/reference/licence).
