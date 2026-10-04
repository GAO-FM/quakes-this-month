# PROCESS.md

## Tools used

- **Doubao**: writing `fetch.py` and `plot.py`, debugging, and iterating on the look of the picture.
- **uv** to run the scripts and install exactly what they declare (matplotlib, numpy).
- **PIL**, via a throwaway one-liner that is not part of the repo, to crop regions of the output and actually look at what the code drew.

## What I kept

The scratch metaphor. The obvious chart is a scatter of dots — magnitude as dot size, depth as colour — and it works, but it looks like a news screenshot and says nothing a caption could not. Turning every earthquake into a short scratch whose length and width come from the magnitude keeps exactly the same numbers and makes the plate boundaries read as cracks in a dark plate, which is what an earthquake is, visually. I also kept a log scale on depth: with a linear scale, the roughly 80% of events that happen in the top 50 km of crust all collapse into one colour and the deep subduction zones disappear.

## What I rejected

- **The dot map** — correct but uninteresting, and it is the picture everyone has already seen.
- **A line chart of earthquakes per day** — it is a real transformation of the data, but it throws away geography, the one dimension that makes a month of quakes worth looking at, and 30 points is not much of a line.
- **pandas** for reading the GeoJSON — the file is nested JSON, not a table; the standard library `json` module reads it with fewer moving parts and no silent type coercion.
- **Cartopy/basemap for coastlines** — a real map would anchor the picture, but it adds heavy dependencies for an image that is deliberately a plate, not a globe; the 30-degree graticule is enough.

## What the model got wrong, and what I fixed

A model wrote most of the plotting code; the corrections are the part that is mine.

1. **Negative magnitudes.** The first run printed `RuntimeWarning: invalid value encountered in power`. The USGS feed genuinely contains events with negative magnitude (down to −1.2 — very small slips), and `mag ** 1.3` is NaN for a negative base. Fixed by flooring the magnitude at 0.1 for the size calculation. Left unfixed, those segments would have become NaN and been silently dropped — the picture would have lied by omission.
2. **Flat alpha.** The first version gave every scratch the same opacity; after cropping the output to inspect it, the newest events were indistinguishable from last month's. I folded time in as brightness (alpha grows with recency) so all four dimensions of the data — position, magnitude, depth, time — are in the picture.

## Honest summary

Most of the code is a model's. The useful work was deciding what the picture should mean before letting it draw, and then finding the one real bug — negative magnitudes — that would have made it silently wrong.