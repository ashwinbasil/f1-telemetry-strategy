# F1 Telemetry & Strategy Analytics

**Status: 🚧 In Progress**

Portfolio project applying data analysis skills to motorsport telemetry, vehicle dynamics, and race strategy. Built to break into motorsport data analyst / performance engineer roles.

## Stack

Python, FastF1, DuckDB, Docker, Pandas, NumPy, SciPy, Matplotlib, Plotly

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
Feature Engineering  ✅ COMPLETE
• Corner detection
• Brake points
• Throttle points
• Sector splits
• Delta time
    │
    ▼
Telemetry Analytics  🚧 IN PROGRESS
• Lap comparison
• Driver comparison
• Time loss analysis
• Corner ranking
    │
    ▼
Strategy Engine  ⬜ PLANNED
• Tire degradation model
• Monte Carlo simulation
• Pit stop optimizer
    │
    ▼
Dashboard  ⬜ PLANNED
• Lap comparison view
• Strategy visualizer
```

## Progress

**Done:**
- Docker + Docker Compose environment
- FastF1 ingestion pipeline (laps + telemetry data)
- DuckDB storage layer
- Corner detection (Savitzky-Golay smoothing + local minima detection on speed trace)
- Brake point detection (braking zone start distance, per corner)
- Throttle point detection (corner exit, throttle reapplication point)
- Sector split parsing (all drivers, full race)
- Delta time analysis (point-by-point time gap between two drivers)

**Data used so far:** 2024 Bahrain Grand Prix (Race), Verstappen + Leclerc telemetry, all 20 drivers' lap/sector data.

**Next up:** Telemetry Analytics layer — lap comparison, driver comparison, time loss breakdown, corner-by-corner ranking.

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

## Setup

```bash
docker-compose build
docker-compose up
```

Jupyter available at `localhost:8888`.

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
│   ├── analytics/       # (next layer)
│   ├── strategy/        # (planned)
│   └── dashboard/       # (planned)
├── notebooks/
└── tests/
```

## Why this project

Background in data analysis, no prior motorsport domain experience. Built this to learn vehicle dynamics, telemetry analysis, and race strategy terminology hands-on, using real F1 data, not toy datasets.