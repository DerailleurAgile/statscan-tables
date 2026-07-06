"""
cube_metadata.py — Cached StatsCan cube metadata for vector discovery (SKILL.md Step 1).
Standard library only.

Usage:
  python cube_metadata.py <PID> [--grep keyword] [--all] [--refresh]

Prints the cube title, end date, and each dimension's members (id + name) so a
plain-language series description can be matched to a coordinate. Responses are
cached on disk for 30 days — cube structures rarely change — so repeat discovery
doesn't re-download. --refresh bypasses the cache; deleting the cache dir is
always safe. Large dimensions (>40 members) are summarised unless --all or
--grep is given.

Cache location: %LOCALAPPDATA%/statscan-tables/cube-cache (Windows) or
~/.cache/statscan-tables/cube-cache.
"""
import argparse
import json
import os
import time
from pathlib import Path

from wds_fetch import _post

WDS_METADATA_URL = "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"
MAX_AGE_DAYS = 30
LARGE_DIMENSION = 40


def cache_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".cache")
    return Path(base) / "statscan-tables" / "cube-cache"


def get_cube_metadata(pid: int, refresh: bool = False) -> dict:
    """Cube metadata for a PID, from disk cache when fresh (< MAX_AGE_DAYS old)."""
    path = cache_dir() / f"{pid}.json"
    if not refresh and path.exists():
        age_days = (time.time() - path.stat().st_mtime) / 86400
        if age_days < MAX_AGE_DAYS:
            print(f"[cache] {path} ({age_days:.0f} days old)")
            return json.loads(path.read_text(encoding="utf-8"))
    obj = _post(WDS_METADATA_URL, {"productId": pid})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")
    print(f"[network] fetched and cached to {path}")
    return obj


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pid", type=int, help="product ID, e.g. 18100004")
    ap.add_argument("--grep", default="", help="only show members whose name contains this (case-insensitive)")
    ap.add_argument("--all", action="store_true", help="show every member of large dimensions")
    ap.add_argument("--refresh", action="store_true", help="bypass the cache")
    opts = ap.parse_args()

    obj = get_cube_metadata(opts.pid, opts.refresh)
    print(f"Title: {obj['cubeTitleEn']}")
    print(f"Range: {obj.get('cubeStartDate')} to {obj.get('cubeEndDate')}  (frequency code {obj.get('frequencyCode')})")

    for dim in obj["dimension"]:
        members = dim["member"]
        print(f"\nDIM {dim['dimensionPositionId']}: {dim['dimensionNameEn']} ({len(members)} members)")
        if opts.grep:
            shown = [m for m in members if opts.grep.lower() in m["memberNameEn"].lower()]
        elif len(members) > LARGE_DIMENSION and not opts.all:
            print(f"   ... {len(members)} members — use --grep or --all to list")
            continue
        else:
            shown = members
        for m in shown:
            print(f"   {m['memberId']}  {m['memberNameEn']}")


if __name__ == "__main__":
    main()
