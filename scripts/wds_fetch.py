"""
wds_fetch.py — Fetch a Statistics Canada WDS vector and emit a clean,
chronologically-ordered two-column (Date, Value) file. Standard library only.

Usage: python wds_fetch.py [vectorId] [months] [--transform yoy|raw]
                           [--aggregate monthly|bimonthly|quarterly|annual]
                           [--agg-method mean|sum]
                           [--out statscan_series.csv]
Default: vector 41690974 (CPI Food, Canada, NSA, 2002=100), 24 months, YoY.

YoY is computed as (value_t / value_{t-1yr} - 1) x 100, matched to the same
calendar period a year prior (not simply the 12th-prior row, in case of gaps),
rounded to 1 decimal — StatsCan's own publication precision for CPI YoY. The
Value column header is built from the vector's own series title and table
number plus the actual output date range, so the file carries its provenance
with it. Output is tab-delimited for painless spreadsheet pasting.

Vendored verbatim into statscan-to-pbc/scripts/wds_fetch.py via that project's
scripts/vendor_sync.py — changes here propagate on the next sync run.
"""
import argparse
import csv
import io
import json
import platform
import subprocess
from statistics import fmean
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
    """points: list of WDS datapoint dicts. Returns [(label, value), ...], chronological,
    non-values dropped — the raw series, no transformation. Month-start refPers collapse to
    'YYYY-MM'; true sub-monthly (e.g. weekly) refPers keep the full 'YYYY-MM-DD' so aggregate()
    can bucket them — a series is only monthly-or-coarser if every point lands on day 1."""
    clean = []
    for p in points:
        # statusCode 0 = normal value; 1 = not available; skip non-values
        if p.get("statusCode") in (1, 2, 8, 9):
            continue
        # scalarFactorCode 0 = units; anything else needs scaling (never true for CPI)
        if p.get("scalarFactorCode", 0) != 0:
            raise RuntimeError(f"Unexpected scalar factor {p['scalarFactorCode']} at {p['refPer']}")
        clean.append((p["refPer"][:10], float(p["value"])))
    clean.sort(key=lambda t: t[0])  # chronological; time series must be in time order
    if all(d.endswith("-01") for d, _ in clean):
        clean = [(d[:7], v) for d, v in clean]  # monthly or coarser: label by month
    return clean

def aggregate(series: list, freq: str, method: str = "mean") -> list:
    """series: [(date, value), ...] chronological, dates 'YYYY-MM' or 'YYYY-MM-DD'.
    Compiles into calendar buckets — freq 'monthly'|'bimonthly'|'quarterly'|'annual',
    labelled 'YYYY-MM'/'YYYY-Bn'/'YYYY-Qn'/'YYYY' — via mean (indexes, rates) or
    sum (counts). Incomplete buckets are dropped: month-labelled input by exact
    count (2/3/12 points per bucket), day-labelled input (weekly etc.) by trimming
    the first and last bucket, the only ones the fetch window can cut."""
    span = {"monthly": 1, "bimonthly": 2, "quarterly": 3, "annual": 12}[freq]
    buckets = {}  # insertion-ordered, so chronological like the input
    for d, v in series:
        n = (int(d[5:7]) - 1) // span
        label = {1: f"{d[:4]}-{n+1:02d}", 2: f"{d[:4]}-B{n+1}",
                 3: f"{d[:4]}-Q{n+1}", 12: d[:4]}[span]
        buckets.setdefault(label, []).append(v)
    compile_ = {"mean": fmean, "sum": sum}[method]
    labels = list(buckets)
    if len(series[0][0]) > 7:
        labels = labels[1:-1]
    else:
        labels = [l for l in labels if len(buckets[l]) == span]
    return [(l, compile_(buckets[l])) for l in labels]

def yoy_series(series: list) -> list:
    """series: [(label, value), ...] chronological, label starting with the year
    ('YYYY', 'YYYY-MM', 'YYYY-Qn', ...). Returns [(label, yoy_pct), ...] vs. the same
    label one year earlier, in percentage points rounded to 1 decimal (e.g. 3.8 = 3.8%)."""
    by_label = dict(series)
    out = []
    for label, val in series:
        prior = str(int(label[:4]) - 1) + label[4:]
        if prior in by_label:
            out.append((label, round((val / by_label[prior] - 1.0) * 100, 1)))
    return out

def copy_to_clipboard(text: str) -> bool:
    """Best-effort clipboard copy using the platform's own tool — no dependencies.
    clip (Windows, fed UTF-16 so accents survive), pbcopy (macOS), xclip/xsel (Linux).
    Returns False silently if no tool is available."""
    system = platform.system()
    if system == "Windows":
        # BOM-less UTF-16LE: clip.exe reads it as Unicode without leaving a
        # stray U+FEFF at the front of the pasted text
        candidates = [(["clip"], text.encode("utf-16-le"))]
    elif system == "Darwin":
        candidates = [(["pbcopy"], text.encode("utf-8"))]
    else:
        candidates = [(["xclip", "-selection", "clipboard"], text.encode("utf-8")),
                      (["xsel", "--clipboard", "--input"], text.encode("utf-8"))]
    for cmd, payload in candidates:
        try:
            subprocess.run(cmd, input=payload, check=True)
            return True
        except (OSError, subprocess.CalledProcessError):
            continue
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("vector", nargs="?", type=int, default=41690974)
    ap.add_argument("months", nargs="?", type=int, default=24)
    ap.add_argument("--transform", choices=["yoy", "raw"], default="yoy")
    ap.add_argument("--aggregate", choices=["monthly", "bimonthly", "quarterly", "annual"],
                    default="",
                    help="compile the fetched series into coarser calendar buckets before any "
                         "transform (weekly source: monthly/quarterly/annual; monthly source: "
                         "bimonthly/quarterly/annual); incomplete edge buckets are dropped")
    ap.add_argument("--agg-method", choices=["mean", "sum"], default="mean",
                    help="how each bucket is compiled: mean for indexes and rates (default), "
                         "sum for counts and flows")
    ap.add_argument("--out", default="statscan_series.csv")
    ap.add_argument("--no-clip", action="store_true",
                    help="don't copy the result to the clipboard (e.g. in scheduled jobs)")
    opts = ap.parse_args()

    extra = 12 if opts.transform == "yoy" else 0  # YoY needs a trailing year of source periods
    series = clean_points(fetch_vector(opts.vector, opts.months + extra))
    agg_label = f"{opts.aggregate.title()} {opts.agg_method.title()} " if opts.aggregate else ""
    if opts.aggregate:
        series = aggregate(series, opts.aggregate, opts.agg_method)
    if opts.transform == "yoy":
        series = yoy_series(series)
        if not series:
            raise SystemExit("YoY needs a same-period-prior-year match, which sub-monthly dates "
                             "won't have — aggregate first, e.g. --aggregate monthly")
        transform_label = agg_label + "YoY % Change"
    else:
        transform_label = agg_label.strip() or "Raw"

    title, table = fetch_series_info(opts.vector)
    header = build_header(title, table, transform_label, series[0][0], series[-1][0],
                          compiled=bool(opts.aggregate))

    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", lineterminator="\n")
    w.writerow(["Date", header])
    w.writerows(series)
    text = buf.getvalue()

    with open(opts.out, "w", newline="", encoding="utf-8") as f:
        f.write(text)

    # Verification block: exact series title, range, spot-check values
    print(f"Wrote {len(series)} rows to {opts.out}")
    if not opts.no_clip and copy_to_clipboard(text):
        print("Copied to clipboard — paste straight into Excel, Sheets, or a text file.")
    print(f"Series:  {transform_label} {title} (Table {table}, v{opts.vector})")
    print(f"Range:   {series[0][0]} to {series[-1][0]}")
    print(f"Last 3:  " + ", ".join(f"{d}: {v}" for d, v in series[-3:]))

if __name__ == "__main__":
    main()
