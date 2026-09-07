# F1 Telemetry & Strategy Analytics

**Status: Core pipeline complete, scaled to full grid + 8 races (2024 season).**

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
Feature Engineering  ✅ (Bahrain, full grid)
• Corner detection, brake points, throttle points, sector splits, delta time
    │
    ▼
Telemetry Analytics  ✅ (Bahrain, full grid)
• Lap comparison, corner ranking, driver comparison, time loss report
    │
    ▼
Strategy Engine  ✅ (full grid, all 8 races)
• Tire degradation model (per race, per compound)
• Monte Carlo simulation (310 scenarios across 8 races)
• Pit stop optimizer (best strategy per race)
    │
    ▼
Dashboard  ✅
• Single self-contained HTML file (Plotly, CDN-based, no server needed)
• Race-filterable tire degradation chart, 8-race pit strategy summary
• Hosted live via GitHub Pages
```

## Scope

- **Drivers:** full 20-driver grid
- **Races:** 8 races, 2024 season — Bahrain, Saudi Arabia, Australia, Monaco, Singapore, Belgium, Japan, Monza (Italian GP)
- **Season:** 2024 only, single year
- **Note:** Feature Engineering and Telemetry Analytics layers currently cover Bahrain only; Strategy Engine (degradation, Monte Carlo, pit optimizer) covers all 8 races.

## Results

**Bahrain GP 2024 (full grid):**
- Fastest: VER (92.608s) — Slowest: OCO (96.226s) — field spread 3.618s
- Top corner by avg time lost across field: Corner 1 (0.364s vs fastest driver)
- Optimal pit strategy: HARD → HARD, pit lap 28, predicted race time 5645.34s

**Across 8 races — tire degradation validated against real physics on:**
- Bahrain: SOFT 0.128 vs HARD 0.056 sec/lap
- Japan: SOFT 0.152 > MEDIUM 0.131 > HARD 0.070 sec/lap
- Singapore: SOFT 0.073 vs HARD 0.016 sec/lap

## Key engineering decisions & debugging

**Tire degradation fuel/track-evolution confound.** Initial model showed HARD compound as faster base pace than SOFT, contradicting real tire physics. Root cause: the regression intercept conflated compound pace with fuel load. Fixed by computing a global fuel-burn/track-evolution trend per race, then normalizing each stint's base laptime to a common reference point before averaging by compound.

**Multi-race scaling surfaced a real model limitation.** Extending the degradation model to 8 races, only 3 (Bahrain, Japan, Singapore) validate cleanly against known tire physics. Australia, Monaco, Monza, Saudi Arabia, and Belgium show near-zero or negative fitted degradation rates. Tried filtering to green-flag-only laps via the `TrackStatus` column; this didn't resolve it. Most likely cause: low sample size per stint combined with genuinely low real-world tire degradation at these circuits — Monaco in particular is famously the lowest-degradation circuit on the calendar, so a near-zero fitted rate there is arguably more correct than a forced-positive number would be. This limitation propagates downstream as expected: the pit optimizer picks SOFT→SOFT for Australia and Monaco, following the (unreliable) input data rather than masking it.

**Data source name collisions.** Requesting "Italy" as a race name from FastF1 pulled the wrong 2024 event (Emilia Romagna GP at Imola instead of the Italian GP at Monza) — 2024 had two Italian rounds. Fixed by using the specific circuit-based name ("Monza") FastF1 expects.

**Throttle point detection and corner detection false positives** — see commit history / earlier notes; both fixed via edge-buffer and threshold tuning rather than filtering on the wrong signal.

## Known limitations

- **Tire degradation model unreliable on 5 of 8 circuits** (Australia, Monaco, Monza, Saudi Arabia, Belgium) — documented above, reliable on Bahrain, Japan, Singapore.
- **Feature Engineering / Telemetry Analytics layers still Bahrain-only** — corner detection, brake/throttle points, and driver comparison have not been re-run across all 8 races.
- **Corner numbering is slightly uneven across drivers** — 8 corners for most, 9 for some, depending on noise at borderline detections.
- **Linear degradation model, no tire cliff** — assumes constant linear wear, real tires can drop off suddenly past a threshold age.
- **Pit loss time is a fixed constant across all races** — real pit loss varies by track (pit lane length, speed limit zones).

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
│   ├── strategy/        # tire degradation, Monte Carlo, pit optimizer — all scaled to 8 races
│   └── dashboard/       # HTML dashboard builder, with race filter
├── notebooks/
└── tests/
```

## Roadmap

- [x] Scale to full 20-driver grid
- [x] Scale ingestion, tire degradation, Monte Carlo, and pit optimizer to 8 races (2024)
- [x] Rebuild dashboard with a race filter and 8-race strategy data
- [ ] Scale Feature Engineering / Telemetry Analytics to all 8 races (not just Bahrain)
- [ ] Add tire-cliff modeling (non-linear degradation past a threshold age)
- [ ] Per-track pit loss constants instead of one fixed value
- [ ] Expand beyond the 2024 season (multi-year)

## Why this project

Background in data analysis, no prior motorsport domain experience. Built this to learn vehicle dynamics, telemetry analysis, and race strategy terminology hands-on, using real F1 data, not toy datasets. Every layer was built and validated against known motorsport physics rather than assumed correct just because the code ran — including honest documentation of where the model breaks down (5 of 8 circuits) rather than hiding it.