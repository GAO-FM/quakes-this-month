# /// script
# requires-python = ">=3.10"
# ///

"""Fetch the USGS earthquake feed once and save it, unchanged, to data/.

Run once:  uv run fetch.py
The committed file in data/ is what plot.py reads, so the picture can be
rebuilt with no internet connection. This script uses only the standard
library, so it needs nothing to be installed.
"""

import json
from pathlib import Path
from urllib.request import urlopen

# USGS "all month" GeoJSON feed: every earthquake recorded in the past
# 30 days, all magnitudes, updated every minute. No key, no login.
URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"
RAW = Path(__file__).resolve().parent / "data" / "all_month.geojson"


def fetch(url: str, timeout: int = 60) -> bytes:
    """Download a URL and return the bytes exactly as they arrived."""
    with urlopen(url, timeout=timeout) as response:
        return response.read()


def main() -> None:
    payload = fetch(URL)

    # sanity check before anything is committed: it must be a GeoJSON feed
    feed = json.loads(payload.decode("utf-8"))
    title = feed.get("metadata", {}).get("title", URL)
    n = len(feed["features"])
    print(f"ok: {n} features from {title}")

    RAW.write_bytes(payload)  # exact bytes, no reformatting, no renaming
    print(f"saved {len(payload):,} bytes -> {RAW}")


if __name__ == "__main__":
    main()
