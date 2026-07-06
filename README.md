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
  (raw values or YoY % change computed from the index), and print the verification block.
- **`scripts/cube_metadata.py`** — cube discovery with a 30-day disk cache: dimensions and
  members, filterable, so matching a plain-language request to a vector coordinate is one command.
- **`references/known-vectors.md`** — a starter ledger of verified vectors and documented traps
  (CPI food family, emigration components, LFS unemployment). The skill appends to it as new
  series are verified — it's why the second fetch of any series is instant.

## Direct script use (no Claude required)

```
# 24 months of CPI Food YoY, tab-delimited with provenance header
python scripts/wds_fetch.py 41690974 24

# Raw index values instead
python scripts/wds_fetch.py 41690974 24 --transform raw

# What's in a cube? (cached after first call)
python scripts/cube_metadata.py 18100004 --grep "food purchased"
```

## License

MIT — use it freely. Statistics Canada data is subject to the
[Statistics Canada Open Licence](https://www.statcan.gc.ca/en/reference/licence).
