# F1 Telemetry & Strategy Analytics

**Status: Core pipeline complete, scaled to full grid + 8 races.** One data-refresh step pending (see Roadmap).

Portfolio project applying data analysis skills to motorsport telemetry, vehicle dynamics, and race strategy. Built to break into motorsport data analyst / performance engineer roles, starting from zero prior motorsport domain experience.

🔗 [Live Dashboard](https://<your-username>.github.io/f1-telemetry-strategy/)

## Stack

Python, FastF1, DuckDB, Docker, Pandas, NumPy, SciPy, Plotly

## Architecture

```
FastF1 (data source)
    │
    ▼
Data Ingestion  — 20 drivers × 8 races (2024 season)
    │
    ▼
DuckDB (storage)
    │
    ▼
Feature Engineering  ✅
• Corner detection (Savitzky-Golay smoothing + local minima on speed trace)
• Brake points (braking zone start per corner)
• Throttle points (corner exit, throttle reapplication)
• Sector splits (all drivers, full race)
• Delta time (each driver vs session-fastest reference)
    │
    ▼
Telemetry Analytics  ✅
• Lap comparison (speed trace + delta overlay)
• Corner ranking (avg time lost per corner, full grid)
• Driver comparison (race pace + consistency, full grid ranked)
• Time loss report (aggregate summary)
    │
    ▼
Strategy Engine  ✅ (Bahrain-specific; multi-race deg model built, other strategy pieces not yet re-run at 8-race scale)
• Tire degradation model (lap time vs tyre age, per compound, per race)
• Monte Carlo simulation (1000 trials per pit-lap/compound combo)
• Pit stop optimizer (best strategy recommendation)
    │
    ▼
Dashboard  ✅
• Single self-contained HTML file (Plotly, CDN-based, no server needed)
• Hosted live via GitHub Pages
```

## Scope

- **Drivers:** full 20-driver grid
- **Races:** 8 races, 2024 season — Bahrain, Saudi Arabia, Australia, Monaco, Singapore, Belgium, Japan, Monza (Italian GP)
- **Season:** 2024 only, single year

## Results (Bahrain GP 2024, full grid)

- Fastest: VER (92.608s) — Slowest: OCO (96.226s) — field spread 3.618s
- Top corner by avg time lost across field: Corner 1 (0.364s vs fastest driver)
- Optimal pit strategy: HARD → HARD, pit lap 30, predicted race time 5546.75s
- Tire degradation validated against real physics on Bahrain: SOFT degrades ~2.2x faster than HARD (0.128 vs 0.056 sec/lap)

## Key engineering decisions & debugging

**Tire degradation fuel/track-evolution confound.** Initial model showed HARD compound as faster base pace than SOFT, contradicting real tire physics. Root cause: the regression intercept conflated compound pace with fuel load, since SOFT stints were mostly early (heavy fuel) and HARD stints mostly late (light fuel). Fixed by computing a global fuel-burn/track-evolution trend per race via regression on lap number, then normalizing each stint's base laptime to a common reference point before averaging by compound.

**Multi-race scaling surfaced a real model limitation.** Extending the degradation model to Australia and Saudi Arabia (both known low-degradation circuits) produced near-zero or negative fitted degradation rates — physically implausible on the surface. Tried filtering to green-flag-only laps via the `TrackStatus` column; this didn't resolve it. Most likely cause: low sample size per stint combined with genuinely low real-world tire degradation at these circuits, so fuel-burn noise dominates whatever degradation signal exists. The model remains reliable on high-degradation circuits (Bahrain) and is documented as unreliable on low-degradation ones, rather than force-fit with more parameters.

**Throttle point detection returning zero coasting distance.** Early version of corner-exit throttle detection returned 0m coasting length for every corner, because the search window included the apex point itself, where throttle had already ticked above threshold. Fixed by excluding the apex point and starting the search strictly after it.

**Corner detection false positives.** Raw local-minima detection on the speed trace initially found extra "corners," including a track-boundary artifact near distance 0. Fixed with an edge buffer and a minimum speed-drop threshold, rather than filtering on throttle value (which incorrectly removed a legitimate high-speed corner).

**Data source name collisions.** Requesting "Italy" as a race name from FastF1 pulled the wrong 2024 event (Emilia Romagna GP at Imola instead of the Italian GP at Monza) — 2024 had two Italian rounds. Fixed by using the specific circuit-based name ("Monza") FastF1 expects.

## Known limitations

- **Tire degradation model unreliable on low-degradation circuits** (Australia, Saudi Arabia) — see above. Reliable on Bahrain.
- **Corner numbering is slightly uneven across drivers** — the corner-detection heuristic finds 8 corners for most drivers and 9 for some, depending on noise in the speed trace at borderline detections.
- **Strategy Engine (Monte Carlo, pit optimizer) is still Bahrain-specific** — not yet re-run across all 8 races.
- **Linear degradation model, no tire cliff** — real tires can show a sudden performance drop past a certain age; this model assumes constant linear wear.
- **Pit loss time is a fixed constant** — real pit loss varies by team, track, and pit lane length.

## Setup

```bash
docker-compose build
docker-compose up
```

Jupyter available at `localhost:8888`.

To regenerate the dashboard:
```bash
docker-compose run app python -m src.dashboard.build_dashboard
```
Output: `data/processed/dashboard.html`

## Project Structure

```
f1-telemetry-strategy/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── ingestion/       # FastF1 data pulls (single-race and multi-race/multi-driver)
│   ├── db/              # DuckDB load scripts
│   ├── features/        # corner/brake/throttle/sector/delta detection, scaled to full grid
│   ├── analytics/       # lap/driver comparison, corner ranking, time loss
│   ├── strategy/        # tire degradation (multi-race), Monte Carlo, pit optimizer
│   └── dashboard/       # HTML dashboard builder
├── notebooks/
└── tests/
```

## Roadmap

- [x] Scale to full 20-driver grid
- [x] Scale ingestion + tire degradation model to 8 races (2024)
- [ ] Regenerate `sector_splits_multi_race` and `tire_degradation_multi_race` from the current 8-race `laps_multi_race` table (currently still reflect the earlier 3-race pull)
- [ ] Re-run Monte Carlo and pit optimizer across all 8 races, not just Bahrain
- [ ] Add a race filter/selector to the dashboard
- [ ] Add tire-cliff modeling (non-linear degradation past a threshold age)
- [ ] Expand beyond the 2024 season (multi-year)

## Why this project

Background in data analysis, no prior motorsport domain experience. Built this to learn vehicle dynamics, telemetry analysis, and race strategy terminology hands-on, using real F1 data, not toy datasets. Every layer was built and validated against known motorsport physics rather than assumed correct just because the code ran — including the honest documentation of where the model breaks down (low-degradation circuits) rather than hiding it.