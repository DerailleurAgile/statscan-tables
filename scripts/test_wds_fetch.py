"""Offline self-check for the clean/transform logic. Standard library only, no network.

Run: python test_wds_fetch.py
"""
from wds_fetch import clean_points, to_yoy, build_header


def dp(ref, value, status=0, scalar=0):
    return {"refPer": f"{ref}-01", "value": value, "statusCode": status, "scalarFactorCode": scalar}


def main():
    # clean_points: sorts chronologically, drops non-values
    points = [dp("2025-02", 102.0), dp("2025-01", 101.0), dp("2025-03", 0, status=1)]
    assert clean_points(points) == [("2025-01", 101.0), ("2025-02", 102.0)]

    # to_yoy: matched to same calendar month a year prior, percent to 1 decimal
    points = [dp("2024-01", 100.0), dp("2024-02", 100.0), dp("2025-01", 103.8), dp("2025-02", 97.0)]
    assert to_yoy(points) == [("2025-01", 3.8), ("2025-02", -3.0)]

    # to_yoy: a gap in the prior year produces no output row, not a wrong comparison
    points = [dp("2024-01", 100.0), dp("2025-01", 102.0), dp("2025-02", 105.0)]
    assert to_yoy(points) == [("2025-01", 2.0)]

    # header carries transform, range, and provenance
    h = build_header("Food", "18-10-0004", "YoY % Change", "2025-01", "2026-05")
    assert h == "StatsCan: YoY % Change Food (2025-01-2026-05) — Table: 18-10-0004"
    h = build_header("Emigrants", "17-10-0040", "Estimated Annual", "2010", "2025", compiled=True)
    assert "Compiled from Table: 17-10-0040" in h

    print("All checks pass.")


if __name__ == "__main__":
    main()
