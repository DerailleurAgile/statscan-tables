"""Offline self-check for the clean/transform/aggregate logic. Standard library only, no network.

Run: python test_wds_fetch.py
"""
from wds_fetch import clean_points, aggregate, yoy_series, build_header


def dp(ref, value, status=0, scalar=0):
    return {"refPer": f"{ref}-01", "value": value, "statusCode": status, "scalarFactorCode": scalar}


def main():
    # clean_points: sorts chronologically, drops non-values, collapses month-start refPers
    points = [dp("2025-02", 102.0), dp("2025-01", 101.0), dp("2025-03", 0, status=1)]
    assert clean_points(points) == [("2025-01", 101.0), ("2025-02", 102.0)]

    # clean_points: true sub-monthly (e.g. weekly) refPers keep the day, for aggregate() to bucket
    weekly = [{"refPer": "2025-01-12", "value": "2", "statusCode": 0, "scalarFactorCode": 0},
              {"refPer": "2025-01-05", "value": "1", "statusCode": 0, "scalarFactorCode": 0}]
    assert clean_points(weekly) == [("2025-01-05", 1.0), ("2025-01-12", 2.0)]

    # yoy_series: matched to the same calendar period a year prior, percent to 1 decimal
    monthly = [("2024-01", 100.0), ("2024-02", 100.0), ("2025-01", 103.8), ("2025-02", 97.0)]
    assert yoy_series(monthly) == [("2025-01", 3.8), ("2025-02", -3.0)]

    # yoy_series: a gap in the prior year produces no output row, not a wrong comparison
    assert yoy_series([("2024-01", 100.0), ("2025-01", 102.0), ("2025-02", 105.0)]) == [("2025-01", 2.0)]

    # yoy_series: generalizes across label shapes, not just monthly
    assert yoy_series([("2023-Q1", 100.0), ("2024-Q1", 104.0)]) == [("2024-Q1", 4.0)]
    assert yoy_series([("2023", 100.0), ("2024", 102.0)]) == [("2024", 2.0)]

    # aggregate: monthly -> quarterly mean, leading partial quarter (Feb-Mar only) dropped
    m = [(f"2023-{i:02d}", float(i)) for i in range(2, 13)]  # Feb..Dec 2023
    assert aggregate(m, "quarterly") == [("2023-Q2", 5.0), ("2023-Q3", 8.0), ("2023-Q4", 11.0)]

    # aggregate: monthly -> annual sum, and bimonthly mean with a trailing partial bucket dropped
    assert aggregate([(f"2023-{i:02d}", 1.0) for i in range(1, 13)], "annual", "sum") == [("2023", 12.0)]
    assert aggregate([("2023-01", 1.0), ("2023-02", 3.0), ("2023-03", 5.0)], "bimonthly") == [("2023-B1", 2.0)]

    # aggregate: weekly (day-labelled) -> monthly, possibly-partial edge buckets trimmed
    w = ([(f"2023-01-{d:02d}", 1.0) for d in (7, 14, 21, 28)]
         + [(f"2023-02-{d:02d}", 2.0) for d in (4, 11, 18, 25)]
         + [(f"2023-03-{d:02d}", 3.0) for d in (4, 11)])
    assert aggregate(w, "monthly") == [("2023-02", 2.0)]

    # header carries transform, range, and provenance
    h = build_header("Food", "18-10-0004", "YoY % Change", "2025-01", "2026-05")
    assert h == "StatsCan: YoY % Change Food (2025-01-2026-05) — Table: 18-10-0004"
    h = build_header("Emigrants", "17-10-0040", "Estimated Annual", "2010", "2025", compiled=True)
    assert "Compiled from Table: 17-10-0040" in h

    print("All checks pass.")


if __name__ == "__main__":
    main()
