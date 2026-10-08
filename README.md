# F1 Telemetry & Race Strategy Analytics

🔗 **[Live Dashboard](https://ashwinbasil.github.io/f1-telemetry-strategy/)**

An analytics system that takes raw Formula 1 timing and telemetry data and turns it into answers a race team would actually ask: *Where is time being lost? How fast do the tyres wear out? When should we pit, and on what tyres?*

Covers the full grid across 8 circuits and 2 seasons (2023 and 2024). Built as a portfolio project to move into motorsport data analysis, starting from zero prior motorsport domain knowledge.

---

# Part 1: For stakeholders

*If you only read one part, read this one. It covers what the system tells you, what you can trust, and what you shouldn't lean on yet.*

## The questions it answers

| Question | What the system gives you |
|---|---|
| Where on track is a driver losing time to the fastest car? | Corner-by-corner time loss, ranked, for every driver and every race |
| How quickly do each tyre compound wear out at this circuit? | Degradation rate per compound, per race, per season |
| Do tyres fall off a cliff late in a stint, and when? | Detected cliff points per compound (23% of long stints show one) |
| How much does a pit stop really cost at this track? | Per-circuit pit loss, from about 8.5 to 18.5 seconds depending on the track |
| What's the best pit stop strategy? | Optimal pit lap and compound choice per race, from 725 simulated scenarios |

## The headline finding

**At Bahrain, the model recommends the same strategy in both seasons: start on HARD, pit around lap 28, finish on HARD.** The 2023 and 2024 results were fitted completely independently, so agreement between them is real evidence rather than a coincidence of one dataset.

More importantly, that recommendation **did not change** when the underlying model was made progressively more realistic:

1. A basic model assuming tyres wear at a constant rate
2. The same model with pit-stop cost measured per circuit from real timing data, with stops made under safety cars excluded
3. A model where tyres can fall off a cliff late in a stint, used in 70% of all simulated scenarios

A recommendation that survives three independent challenges is one you can put weight on. That's the single most decision-relevant result here.

## Other findings worth knowing

- **Hot tracks hurt soft tyres the most.** Degradation depends on tyre age *and* track temperature together, and the soft compound is the most heat-sensitive of the three, which matches how tyre chemistry is known to work.
- **Pit stop cost varies a lot by circuit**, from about 8.5 seconds at Australia to 18.4 seconds at Singapore. Using one number for every track would distort strategy calls.
- **Safety cars were distorting pit-cost estimates.** At Saudi Arabia, 14 of 24 pit stops happened under caution, which inflated the apparent cost from 9.5 to 31.6 seconds. Filtering them out fixed it.
- **Bahrain 2024:** Verstappen set the fastest lap (92.608s), Ocon the slowest of the grid (96.226s), a 3.6-second spread. Turn 1 cost the field the most time, an average of 0.36s against the fastest driver.

## How far to trust it

| Confidence | What |
|---|---|
| **Higher** | Bahrain and Japan tyre behaviour, which holds up in both seasons. Corner time-loss rankings. Per-circuit pit cost as a relative comparison between tracks. |
| **Lower** | Tyre wear at low-degradation circuits (e.g. Monaco, Australia), where the signal is too weak against the noise. Treat the strategy output there as indicative only. |
| **Treat as approximate** | Pit cost figures, accurate to roughly ±3-5 seconds. 2023 pit costs reuse the 2024-derived values. |
| **Not yet validated** | The strategy recommendations have **not** been checked against what teams actually did or how races actually finished. See below. |

## What this system cannot tell you (yet)

**It has not been backtested against real race results.** The official finishing-order data source (Ergast) returns nothing for any 2023 or 2024 race, confirmed across all 16 races tested. I tried deriving winners from lap times as a workaround and it produced clearly wrong winners (drivers who never won those races), so I stopped rather than present a backtest built on bad data. Closing this gap needs a different results data source.

Practical meaning: the system is good at *comparing options and ranking them*, and not yet proven at *predicting what will happen in a real race*. It does not model traffic, safety cars during the race, or track position, all of which shape real strategy calls.

## Recommended use

- **Use now:** comparing circuits, ranking where time is lost, understanding tyre behaviour at high-degradation tracks, sanity-checking a strategy idea.
- **Do not use yet:** as the sole basis for a live strategy call, until it is validated against real outcomes.

## Reading the dashboard

The [live dashboard](https://ashwinbasil.github.io/f1-telemetry-strategy/) has five views. The corner-ranking and tyre-degradation charts each have a dropdown to switch between any of the 16 race-and-year combinations. The pit-strategy chart shows the recommended strategy and predicted race time for all 16 at once.

---

# Part 2: For engineers

*Architecture, method, debugging history, and how to run it.*

## Stack

Python, FastF1, DuckDB, Docker, Pandas, NumPy, SciPy, Plotly

## Architecture

```
FastF1 (data source)
    │
    ▼
Data Ingestion  — 20+ drivers × 8 races × 2 seasons (2023, 2024) + weather
    │
    ▼
DuckDB (storage)
    │
    ▼
Feature Engineering
• Corner detection (Savitzky-Golay smoothing + local minima on speed trace)
• Brake points, throttle points, sector splits
• Delta time vs per-race fastest lap
    │
    ▼
Telemetry Analytics
• Corner ranking (outlier-filtered), driver comparison, time-loss report
    │
    ▼
Strategy Engine
• Linear degradation model — per race / year / compound
• Thermal model — track temp × tyre age, pooled across stints
• Tire-cliff detection (piecewise regression)
• Per-race pit loss (in-lap/out-lap timing, green-flag laps only)
• Monte Carlo — cliff-aware piecewise degradation curve where data exists
• Pit stop optimizer
    │
    ▼
Dashboard (Plotly, single static HTML, GitHub Pages)
```

All layers run across the full grid, 8 races, and both seasons.

## Method notes

**Degradation model.** Per stint, lap time is regressed on tyre age. Each stint's baseline is normalised against a per-race trend in lap number, which strips out fuel burn-off and track evolution so they don't masquerade as compound pace.

**Thermal model.** Lap time is regressed on tyre age, track temperature, and their interaction, pooled across all stints of a compound. Weather is joined to laps with an as-of join on cumulative lap time (100% coverage, 15,848 laps).

**Cliff detection.** A piecewise linear fit is searched over candidate breakpoints per stint (10+ laps). A cliff is flagged only if the post-breakpoint slope is both ≥0.15 s/lap in absolute terms and meaningfully steeper than the pre-breakpoint slope. 142 of 615 stints flagged.

**Monte Carlo.** 1,000 trials per scenario, across 5 pit-lap options and all compound pairs per race/year, with Gaussian lap-time noise. Where a (year, race, compound) group has ≥2 detected-cliff stints, the sim uses a piecewise curve; otherwise it falls back to linear. 510 of 725 scenarios used the cliff curve.

## Debugging log

Each of these was caught by noticing a result that contradicted known physics or common sense, then finding the cause with a measurement rather than a guess.

| Problem | Diagnosis | Fix |
|---|---|---|
| HARD compound looked faster than SOFT | Regression intercept conflated compound pace with fuel load (SOFT stints are early and heavy, HARD stints late and light) | Per-race fuel/track-evolution trend, normalised out before averaging |
| Cliff detector flagged 47% of stints | Relative-slope test fired whenever an early negative (fuel-driven) slope turned barely positive | Added an absolute slope threshold; rate fell to 23% and matched circuit reputations |
| Thermal interaction coefficient negative for every compound | Within-stint tyre age vs track temp correlated at mean \|r\| = 0.674, with 59.5% of stints above 0.7 | Pooled across stints; correlation fell to 0.08-0.19 and coefficients turned positive, SOFT highest |
| Saudi Arabia pit loss 31.6s | 14 of 24 stops were under caution | Filtered to green-flag laps; estimate fell to 9.5s (n=10, so itself uncertain) |
| 2023 Japan corner average 1.42s | One driver (BOT) had a 17.9s delta on a single lap, an incident rather than cornering | Excluded \|delta\| > 2.0s; value corrected to 0.76s. Same driver independently shows as slowest in that race in a separate table |
| 2023 Bahrain "fastest" driver was ZHO | Verified real: the final lap, run alone in clean air | Documented, not corrected |
| "Italy" loaded the wrong race | 2024 had two Italian rounds; FastF1 matched Imola | Request "Monza" explicitly |
| Backtest produced impossible winners | Ergast has no results for 2023/2024; lap-time-sum is not a valid proxy for finishing order | Stopped and documented as a data-source blocker |

## Known limitations

- **No ground-truth validation.** Backtesting is blocked by missing official results (see Part 1).
- **Linear degradation is unreliable on roughly half of circuit/year combinations.** The cliff model compensates only where cliff data exists.
- **Australia's cross-year match broke under the cliff model** (SOFT→SOFT in 2023, HARD→SOFT in 2024). Both years used the linear fallback, so this is most likely Monte Carlo noise on a close call, not investigated further.
- **Bahrain's worst corner differs by year** (Turn 5 in 2023, Turn 1 in 2024) even after outlier filtering. The tyre physics is stable across years; corner-level rankings are not.
- **Pit loss is rough** (±3-5s), small per-race samples after green-flag filtering, and 2023 reuses 2024-derived values.
- **Thermal model INTERMEDIATE/WET rows are noise** (18 and 3 stints).
- **Corner counts vary slightly by driver** (8 or 9 detected), a limitation of the heuristic detector.
- **Simulation omits traffic, mid-race safety cars, and track position.**

## Setup

```bash
docker-compose build
docker-compose up
```

Jupyter at `localhost:8888`. To regenerate the dashboard:

```bash
docker-compose run app python -m src.dashboard.build_dashboard
```

Output: `data/processed/dashboard.html`

## Project structure

```
f1-telemetry-strategy/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
├── docs/                # published dashboard (GitHub Pages)
├── src/
│   ├── ingestion/       # telemetry, laps, weather, race results
│   ├── db/              # DuckDB load, merge, weather-join
│   ├── features/        # corner / brake / throttle / sector / delta
│   ├── analytics/       # driver comparison, corner ranking, time loss
│   ├── strategy/        # degradation, cliffs, pit loss, Monte Carlo, optimizer, backtest (blocked)
│   └── dashboard/       # dashboard builder
├── notebooks/
└── tests/
```

## Open work

- Backtest against real outcomes, once a working results source is found
- Per-circuit 2023 pit loss measured independently rather than reused from 2024
- Extend the thermal model with more wet-weather data

## About this project

Built to learn race strategy and telemetry analysis hands-on with real data. The discipline it practised: don't trust a number because the code ran, check it against what you know should be true, and say plainly where the evidence stops.