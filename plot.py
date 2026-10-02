# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///

"""One scratch per earthquake.

Reads data/all_month.geojson — the USGS feed fetched once by fetch.py — and
draws every earthquake as a short scratch on a dark plate.

    position  -> longitude / latitude (equirectangular projection)
    magnitude -> scratch length and width
    depth     -> colour (shallow: bright, deep: dark)

Output: out/quakes.png
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import LogNorm

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "all_month.geojson"
OUT = ROOT / "out" / "quakes.png"


def load_quakes(path):
    """Return (lon, lat, depth_km, magnitude, days, start_ms) from a USGS feed.

    Events without a magnitude are skipped: the feed leaves mag blank on a
    few records, and a scratch of unknown size would be a lie.
    """
    with open(path, "r", encoding="utf-8") as handle:
        feed = json.load(handle)

    lons, lats, depths, mags, times = [], [], [], [], []
    for feature in feed["features"]:
        magnitude = feature["properties"].get("mag")
        if magnitude is None:
            continue
        lon, lat, depth = feature["geometry"]["coordinates"]
        lons.append(lon)
        lats.append(lat)
        depths.append(depth)
        mags.append(magnitude)
        times.append(feature["properties"]["time"])

    start = min(times)
    days = [(t - start) / 86_400_000 for t in times]
    return (np.array(lons), np.array(lats), np.array(depths),
            np.array(mags), np.array(days), start)


def scratch_segment(angle, length):
    """End points of one scratch centred on the origin, flattened for a map."""
    dx = length * np.cos(angle)
    dy = 0.55 * length * np.sin(angle)
    return np.array([(-dx, -dy), (dx, dy)])


def draw_scale(ax):
    """Sample scratches showing that magnitude controls length and width."""
    x0, y0, gap = 0.012, 0.900, 0.055
    ax.text(x0, y0 + 0.040, "magnitude -> scratch length & width",
            transform=ax.transAxes, color="#7a8396", fontsize=8)
    for i, magnitude in enumerate((3.0, 5.0, 7.0)):
        length = 0.0095 * magnitude ** 1.3
        width = 0.22 * magnitude ** 1.6
        y = y0 - i * gap
        ax.plot([x0, x0 + length], [y, y], transform=ax.transAxes,
                color="#e8eaf0", linewidth=width, solid_capstyle="round")
        ax.text(x0 + length + 0.012, y, f"M{magnitude:.0f}",
                transform=ax.transAxes, color="#7a8396", fontsize=8,
                va="center")


def main():
    lons, lats, depths, mags, days, start_ms = load_quakes(RAW)
    n = len(mags)
    print(f"{n} earthquakes | magnitude {mags.min():.1f}-{mags.max():.1f} "
          f"| depth 0-{depths.max():.0f} km | span {days.max():.0f} days")

    # colour: shallow quakes are bright, deep ones are dark. Log scale,
    # because almost everything happens in the top 50 km of the crust.
    norm = LogNorm(vmin=1.0, vmax=700.0)
    cmap = plt.get_cmap("viridis")
    colours = cmap(1.0 - norm(np.clip(depths, 1.0, 700.0)))

    # recency: newer cracks glow brighter, so time is in the picture too
    age = days / days.max()
    colours[:, 3] = 0.30 + 0.45 * age

    # length and width both grow with magnitude. A few events have negative
    # magnitudes (very small slips); clip them so the size law stays finite.
    size = np.maximum(mags, 0.1)
    length = 0.45 * size ** 1.3
    width = 0.22 * size ** 1.6

    # one scratch per quake; the angle is a fixed pseudo-random draw, so the
    # same data always makes the same picture
    rng = np.random.RandomState(7)
    angles = rng.uniform(0.0, np.pi, size=n)

    segments = np.empty((n, 2, 2))
    for i in range(n):
        segments[i] = scratch_segment(angles[i], length[i]) + (lons[i], lats[i])

    fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
    fig.patch.set_facecolor("#11131a")
    ax.set_facecolor("#11131a")

    # faint graticule every 30 degrees, so the plate reads as a map
    for lon in range(-180, 181, 30):
        ax.axvline(lon, color="#333a4d", lw=0.5, zorder=1)
    for lat in range(-90, 91, 30):
        ax.axhline(lat, color="#333a4d", lw=0.5, zorder=1)
    ax.axhline(0, color="#48516b", lw=0.7, zorder=1)

    collection = LineCollection(segments, linewidths=width, colors=colours,
                                zorder=2)
    collection.set_capstyle("round")
    ax.add_collection(collection)

    ax.set_xlim(-180, 180)
    ax.set_ylim(-70, 85)
    ax.set_aspect(1.0 / np.cos(np.deg2rad(35)))
    ax.set_xticks(range(-180, 181, 30))
    ax.set_yticks(range(-60, 61, 30))
    ax.tick_params(colors="#6a7388", labelsize=7)
    for spine in ax.spines.values():
        spine.set_color("#333a4d")

    start = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc)
    end = datetime.fromtimestamp((start_ms + days.max() * 86_400_000) / 1000,
                                 tz=timezone.utc)
    ax.set_title("One plate, one month of cracks", color="#e8eaf0",
                 fontsize=20, pad=22)
    ax.set_xlabel("longitude - every scratch is one real earthquake (USGS)",
                  color="#6a7388", fontsize=9)

    fig.text(0.5, 0.955,
             f"{n:,} earthquakes  |  {start:%d %b %Y} - {end:%d %b %Y} UTC  "
             f"|  depth 0-{depths.max():.0f} km",
             ha="center", color="#6a7388", fontsize=9)

    draw_scale(ax)

    cbar_sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar_sm.set_array([])
    cbar = fig.colorbar(cbar_sm, ax=ax, fraction=0.025, pad=0.02)
    cbar.ax.tick_params(colors="#6a7388", labelsize=7)
    cbar.set_label("depth / km - bright: shallow, dark: deep",
                   color="#6a7388", fontsize=8)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
