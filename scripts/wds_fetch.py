"""
wds_fetch.py — Fetch a Statistics Canada WDS vector and emit a clean,
chronologically-ordered two-column (Date, Value) file. Standard library only.

Usage: python wds_fetch.py [vectorId] [months] [--transform yoy|raw]
                           [--out statscan_series.csv]
Default: vector 41690974 (CPI Food, Canada, NSA, 2002=100), 24 months, YoY.

YoY is computed as (index_t / index_{t-12} - 1) x 100, matched to the same
calendar month a year prior (not simply the 12th-prior row, in case of gaps),
rounded to 1 decimal — StatsCan's own publication precision for CPI YoY. The
Value column header is built from the vector's own series title and table
number plus the actual output date range, so the file carries its provenance
with it. Output is tab-delimited for painless spreadsheet pasting.
"""
import argparse
import csv
import json
from urllib import request

WDS_DATA_URL = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVectorsAndLatestNPeriods"
WDS_INFO_URL = "https://www150.statcan.gc.ca/t1/wds/rest/getSeriesInfoFromVector"

def _post(url: str, body: dict) -> dict:
    payload = json.dumps([body]).encode()
    req = request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=30) as resp:
        result = json.load(resp)[0]
    if result.get("status") != "SUCCESS":
        raise RuntimeError(f"WDS returned status {result.get('status')}")
    return result["object"]

def fetch_vector(vector_id: int, latest_n: int) -> list:
    return _post(WDS_DATA_URL, {"vectorId": vector_id, "latestN": latest_n})["vectorDataPoint"]

def fetch_series_info(vector_id: int) -> tuple:
    """Returns (series_title, table_code) from the vector's own metadata, e.g. ('Food Purchased
    From Stores', '18-10-0004'). Strips the leading 'Canada;'-style geography prefix and
    title-cases the result, since StatsCan's own SeriesTitleEn is sentence case.

    Trap: for cubes with many dimensions the LAST title segment may be the adjustment type,
    not the series name (see references/known-vectors.md) — override the title when it is."""
    info = _post(WDS_INFO_URL, {"vectorId": vector_id})
    title = info["SeriesTitleEn"].split(";")[-1].strip().title()
    pid = str(info["productId"])
    table = f"{pid[:2]}-{pid[2:4]}-{pid[4:8]}"
    return title, table

def build_header(title: str, table: str, transform: str, start: str, end: str, compiled: bool = False) -> str:
    """'StatsCan: <transform> <title> (<start>-<end>) — <Table:|Compiled from Table:> <table>'.
    Set compiled=True when the output is an aggregate (e.g. quarters summed to years) rather than
    the table's own series as published."""
    prefix = "Compiled from Table" if compiled else "Table"
    return f"StatsCan: {transform} {title} ({start}-{end}) — {prefix}: {table}"

def clean_points(points: list) -> list:
    """points: list of WDS datapoint dicts. Returns [(refPer 'YYYY-MM', value), ...],
    chronological, non-values dropped — the raw series, no transformation."""
    clean = []
    for p in points:
        # statusCode 0 = normal value; 1 = not available; skip non-values
        if p.get("statusCode") in (1, 2, 8, 9):
            continue
        # scalarFactorCode 0 = units; anything else needs scaling (never true for CPI)
        if p.get("scalarFactorCode", 0) != 0:
            raise RuntimeError(f"Unexpected scalar factor {p['scalarFactorCode']} at {p['refPer']}")
        clean.append((p["refPer"][:7], float(p["value"])))
    clean.sort(key=lambda t: t[0])  # chronological; time series must be in time order
    return clean

def to_yoy(points: list) -> list:
    """points: list of WDS datapoint dicts. Returns [(refPer 'YYYY-MM', yoy_pct), ...]
    where yoy_pct is in percentage points rounded to 1 decimal (e.g. 3.8 = 3.8%)."""
    clean = clean_points(points)
    by_month = dict(clean)
    out = []
    for ym, val in clean:
        year, month = int(ym[:4]), int(ym[5:7])
        prior = f"{year-1:04d}-{month:02d}"
        if prior in by_month:
            out.append((ym, round((val / by_month[prior] - 1.0) * 100, 1)))
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("vector", nargs="?", type=int, default=41690974)
    ap.add_argument("months", nargs="?", type=int, default=24)
    ap.add_argument("--transform", choices=["yoy", "raw"], default="yoy")
    ap.add_argument("--out", default="statscan_series.csv")
    opts = ap.parse_args()

    if opts.transform == "yoy":
        series = to_yoy(fetch_vector(opts.vector, opts.months + 12))  # YoY needs 12 trailing months
        transform_label = "YoY % Change"
    else:
        series = clean_points(fetch_vector(opts.vector, opts.months))
        transform_label = "Raw"

    title, table = fetch_series_info(opts.vector)
    header = build_header(title, table, transform_label, series[0][0], series[-1][0])

    with open(opts.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["Date", header])
        w.writerows(series)

    # Verification block: exact series title, range, spot-check values
    print(f"Wrote {len(series)} rows to {opts.out}")
    print(f"Series:  {transform_label} {title} (Table {table}, v{opts.vector})")
    print(f"Range:   {series[0][0]} to {series[-1][0]}")
    print(f"Last 3:  " + ", ".join(f"{d}: {v}" for d, v in series[-3:]))

if __name__ == "__main__":
    main()
