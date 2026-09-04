# F1 Telemetry & Strategy Analytics

**Status: MVP Complete** — end-to-end pipeline built, prototype scope (2 drivers, 1 race). Scaling to full grid + multi-race next.

Portfolio project applying data analysis skills to motorsport telemetry, vehicle dynamics, and race strategy. Built to break into motorsport data analyst / performance engineer roles, starting from zero prior motorsport domain experience.

## Stack

Python, FastF1, DuckDB, Docker, Pandas, NumPy, SciPy, Plotly

## Architecture

```
FastF1 (data source)
    │
    ▼
Data Ingestion
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
• Delta time (point-by-point gap between two drivers)
    │
    ▼
Telemetry Analytics  ✅
• Lap comparison (speed trace + delta overlay)
• Corner ranking (time impact per corner)
• Driver comparison (race pace + consistency)
• Time loss report (aggregate summary)
    │
    ▼
Strategy Engine  ✅
• Tire degradation model (lap time vs tyre age, per compound)
• Monte Carlo simulation (1000 trials per pit-lap/compound combo)
• Pit stop optimizer (best strategy recommendation)
    │
    ▼
Dashboard  ✅
• Single self-contained HTML file (Plotly, CDN-based, no server needed)
```

## Results (Bahrain GP 2024, VER vs LEC)

- Fastest lap gap: 1.315s (LEC slower)
- Top corner by time impact: Corner 1 (+0.415s, LEC faster)
- Optimal pit strategy: HARD → HARD, pit lap 30, predicted race time 5546.75s
- Tire degradation validated against real physics: SOFT degrades ~2.2x faster than HARD (0.1231 vs 0.0563 sec/lap), matches known tire behavior

## Key engineering decisions & debugging

**Tire degradation fuel/track-evolution confound.** Initial model showed HARD compound as faster base pace than SOFT, contradicting real tire physics. Root cause: `base_laptime` (regression intercept) conflated compound pace with fuel load, since SOFT stints in this race were mostly early (heavy fuel) and HARD stints mostly late (light fuel). Fixed by computing a global fuel-burn/track-evolution trend via regression on lap number, then normalizing each stint's base laptime to a common reference point before averaging by compound. Post-fix, SOFT correctly showed faster base pace (97.61s vs 97.84s).

**Throttle point detection returning zero coasting distance.** Early version of corner-exit throttle detection returned 0m coasting length for every corner. Bug was in the search window including the apex point itself, where throttle had already ticked above threshold. Fixed by excluding the apex point and starting the search strictly after it.

**Corner detection false positives.** Raw local-minima detection on speed trace initially found 10 "corners" on an 8-corner-equivalent lap, including a track-boundary artifact at distance ~0 and a shallow noise dip. Fixed with an edge buffer (exclude detections near lap start/end) and a minimum speed-drop threshold, rather than filtering on throttle value (which incorrectly removed a legitimate high-speed corner).

## Known limitations (current scope)

- **2 drivers only (VER, LEC)** — deliberate prototype scope, to validate pipeline logic before scaling. Not a data availability limit; FastF1 has telemetry for the full grid.
- **1 race (Bahrain 2024)** — tire degradation model fit on one track's characteristics; deg rates won't generalize to other circuits without more data.
- **Linear degradation model, no tire cliff** — real tires can show a sudden performance drop past a certain age; this model assumes constant linear wear.
- **Pit loss time is a fixed constant** — real pit loss varies by team, track, and pit lane length.

## DuckDB Tables

| Table | Rows | Description |
|---|---|---|
| `laps` | 1129 | Lap-level data, all 20 drivers |
| `telemetry` | 704 | VER fastest lap, point-by-point |
| `telemetry_lec` | 702 | LEC fastest lap, point-by-point |
| `corners` | 8 | Detected corner apexes |
| `brake_points` | 8 | Braking zone start per corner |
| `throttle_points` | 8 | Throttle reapplication per corner |
| `sector_splits` | 1108 | Parsed sector times, all drivers |
| `delta_ver_lec` | 1000 | Interpolated time delta, VER vs LEC |
| `corner_ranking` | 8 | Corners ranked by time impact |
| `driver_comparison` | 2 | Race pace summary, VER vs LEC |
| `tire_degradation` | 65 | Deg rate + normalized base laptime, per stint |
| `monte_carlo_results` | 20 | Simulated race time per pit-lap/compound combo |
| `pit_optimizer_recommendations` | 4 | Best pit lap per compound strategy |

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
│   ├── ingestion/       # FastF1 data pulls
│   ├── db/              # DuckDB load scripts
│   ├── features/        # corner/brake/throttle/sector/delta detection
│   ├── analytics/       # lap/driver comparison, corner ranking, time loss
│   ├── strategy/        # tire degradation, Monte Carlo, pit optimizer
│   └── dashboard/       # HTML dashboard builder
├── notebooks/
└── tests/
```

## Roadmap

- [ ] Scale to full 20-driver grid (refactor per-driver tables to single table + `Driver` column)
- [ ] Scale to multiple races/years (add `Race`, `Year` columns)
- [ ] Switch delta comparison from pairwise to each-driver-vs-session-fastest reference
- [ ] Add tire-cliff modeling (non-linear degradation past a threshold age)
- [ ] Deploy dashboard via GitHub Pages

## Why this project

Background in data analysis, no prior motorsport domain experience. Built this to learn vehicle dynamics, telemetry analysis, and race strategy terminology hands-on, using real F1 data, not toy datasets. Every layer was built and validated against known motorsport physics (tire compound behavior, corner exit dynamics) rather than assumed correct just because the code ran.s