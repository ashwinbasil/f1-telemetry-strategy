# F1 Telemetry & Race Strategy Analytics 🏎️
**Status:** Core pipeline complete — 20+ drivers, 8 races, 2 seasons (2023–2024), 
with a physics-validated thermal degradation model.


🔗 **[View Live Interactive Dashboard](https://ashwinbasil.github.io/f1-telemetry-strategy/)**
---

## 🎯 Executive Summary
This is an automated, end-to-end predictive analytics pipeline that ingests 
raw Formula 1 telemetry and transforms it into race-winning strategic 
recommendations. The engine answers three high-value operational questions:
1. **When should a driver pit?** — Monte Carlo simulation across 725 scenarios 
   to find the mathematically optimal lap.
2. **Which tires should they run?** — A physics-validated degradation model 
   that accounts for both tyre age *and* track temperature.
3. **Where is time being lost on track?** — Telemetry analysis pinpointing 
   the exact corner costing the most time, across the full 20-driver grid.
Built from zero prior motorsport domain experience to demonstrate 
production-style data engineering, statistical modeling, and 
dashboard delivery.
---

## 💻 Tech Stack
**Python · FastF1 · DuckDB · Docker · Pandas · NumPy · SciPy · Plotly**
---

## 📈 Key Strategic Insights & Business Impact
### 1. Cross-Season Model Validation (Why You Can Trust This)
The most important test of any predictive model is: *does it produce the 
same answer on new data it has never seen?*
This model passes that test. Bahrain and Japan both show the correct physical 
degradation order (SOFT > MEDIUM > HARD) independently in 2023 and 2024 — 
fitted separately, no shared data. The pit optimizer outputs the **identical 
strategy both years**:
- **Bahrain:** HARD → HARD, pit lap 28
- **Australia:** SOFT → SOFT, pit lap 17
Two independently-fit seasons. Same answer both times. That is meaningful 
evidence of a real signal, not statistical noise.
---

### 2. Thermal Degradation Model — The Headline Result

**The business problem:** The original model could predict *average* tire wear but not the sudden late-stint "cliff" — when a tyre suddenly loses 1–2 seconds per lap and the driver radically loses race pace. Knowing when that cliff will happen is worth positions.

**The root cause:** A cliff isn't caused by age alone. It's caused by 
the *combination* of a hot track and an old tyre. Soft rubber on a 
45°C track degrades far faster than the same rubber at 25°C.

**The result:** After solving a collinearity problem in the data 
(see Engineering section), the model correctly quantifies this effect:
| Compound | Heat + Age Sensitivity | Stints Pooled |
|---|---|---|
| **SOFT** | **Highest** (+0.00505) | 121 |
| **HARD** | Medium (+0.00270) | 351 |
| **MEDIUM** | **Lowest** (+0.00097) | 255 |

**Strategic implication:** On a hot circuit like Bahrain, a SOFT tyre 
is not just faster early — it degrades *exponentially* faster late in 
a stint as track temperature combines with tyre age. The model  quantifies the exact crossover point where pitting becomes cheaper than staying out.

---

### 3. Driver Performance & Race Coaching
**Bahrain GP 2024 — Full 20-Driver Grid:**
- **Fastest:** VER (92.608s) · **Slowest:** OCO (96.226s) · Field spread: **3.618s**
- **Highest-priority coaching target:** Corner 1 costs the field an 
  average of **0.364 seconds** vs. the race leader — the single highest-ROI 
  braking zone for simulator training.
- **Cliff detection:** 69 of 302 long stints (10+ laps) show a genuine 
  late-stint acceleration in degradation. Bahrain has the most detected 
  cliffs; Monaco the fewest — matching each circuit's real-world reputation.
---

### 4. Operational Risk: Where the Model Is and Isn't Reliable
| Circuit Type | Model Reliability | Reason |
|---|---|---|
| High-degradation (Bahrain, Japan) | ✅ Reliable, both seasons | Strong signal, sufficient sample size |
| Low-degradation (Monaco, Australia) | ⚠️ Near-zero fitted rates | Fuel-burn noise dominates wear signal |
| Street circuits generally | ⚠️ Use with caution | Low deg + small sample per compound |
| WET / INTERMEDIATE compounds | ❌ Exclude | Only 3–18 stints pooled — insufficient data |

**Operational recommendation:** Use the strategy engine's output directly for Bahrain and Japan. Apply manual validation on low-degradation circuits until the mixed-effects model is implemented.

---

## ⚙️ Technical Implementation (Engineering POV)
### Architecture

```
FastF1 (API: telemetry, laps, weather)
    │
    ▼
Data Ingestion — 20+ drivers × 8 races × 2 seasons (2023, 2024)
    │
    ▼
DuckDB (Analytical Storage)
    │
    ▼
Feature Engineering  ✅ (2024, all 8 races)
· Corner detection · Brake points · Throttle points · Sector splits · Delta time
    │
    ▼
Telemetry Analytics  ✅ (2024, all 8 races)
· Lap comparison · Corner ranking · Driver comparison · Time loss report
    │
    ▼
Strategy Engine  ✅ (Both seasons, all 8 races)
· Linear degradation model (per race / year / compound)
· Thermal degradation model (TyreAge × TrackTemp, pooled across stints)
· Tire-cliff detection (piecewise regression, breakpoint + slope change)
· Per-race pit loss estimation (from real in-lap/out-lap timing)
· Monte Carlo simulation (725 scenarios)
· Pit stop optimizer (best strategy per race/year)
    │
    ▼
Plotly Dashboard  ✅ (Serverless HTML via GitHub Pages)
· Race + year filter · Tire degradation chart · Full pit strategy summary
```

## Scope

- Drivers: Full grid, 20–22 per race (reserve drivers included, e.g., Bearman sub for Sainz at Saudi Arabia 2024)
- Races: Bahrain · Saudi Arabia · Australia · Monaco · Singapore · Belgium · Japan · Monza
- Seasons: 2023 and 2024
- Note: Feature Engineering and Telemetry Analytics cover 2024 only. Strategy Engine covers both seasons.


## 🛠️ Key Engineering Decisions & Debugging

**Fuel-Burn / Track-Evolution Confound**
The initial linear regression showed HARD compound as faster base pace than SOFT — physically backwards. Root cause: the regression intercept conflated compound pace with fuel load, because SOFT stints typically run early (heavy fuel) and HARD stints late (light fuel). Fixed by computing a global fuel-burn trend per race and normalizing each stint's base laptime to a common reference point before fitting by compound.


## Thermal Model Collinearity — Full Diagnosis

**The problem:** Adding TrackTemp and a TyreAge × TrackTemp interaction term to per-stint regression produced uniformly negative interaction coefficients — physically nonsensical (implying heat helps old tyres). Rather than accept the result, measured the cause directly.

**The diagnosis:** Computed Pearson correlation between TyreAge and TrackTemp within every individual stint. Mean |r| = 0.674 across 748 stints; 59.5% of stints exceed |r| = 0.7. Root cause is structural: track temperature drifts monotonically through a race (typically cooling) at exactly the same time tyre age only ever increases. Standard linear regression cannot reliably separate two variables that move in lockstep within a single stint.

**The fix:** Pool stints. Normalise each stint's lap times to its own median first (preventing compound performance from dominating), then combine all stints for a compound into one regression. Pooling across different races breaks the artificial correlation — it dropped from 0.674 to 0.078–0.188 depending on compound. Interaction coefficients flipped to physically correct positive values. SOFT shows the largest interaction (+0.00505), matching real tyre chemistry: softer compounds are the most temperature-sensitive. This is a genuine methodological flaw, diagnosed with a number, fixed with a principled approach that recovered the expected physics.

## Tire-Cliff Detector Calibration

Initial version flagged 47% of stints as having a cliff, because it only required the post-breakpoint slope to be relatively steeper than pre-breakpoint. Any stint going from a fuel-burn-driven flat early slope to a barely-positive late slope got flagged as a cliff. Fixed by adding an absolute magnitude threshold on the post-breakpoint slope (0.15 sec/lap minimum). Detection rate dropped to 23% and the circuit pattern became physically coherent (Bahrain most, Monaco fewest).

## Per-Race Pit Loss Estimation

Estimated from the actual gap between in-lap/out-lap times and normal race pace rather than a fixed constant. Ranges from 11.2s (Belgium/Spa, long fast pit lane) to 31.6s (Saudi Arabia). The Saudi figure is likely inflated by stops taken under safety car — pit-lane time loss during a caution period is much smaller than a green-flag stop, but the current method doesn't filter for this. Flagged, not yet fixed.

## Data Source Name Collision

Requesting "Italy" from FastF1 in 2024 returned the Emilia Romagna GP at Imola, not the Italian GP at Monza — 2024 had two Italian rounds. Fixed by requesting "Monza" directly.

## 🚧 Known Limitations


| Limitation | Status |
| :--- | :--- |
| Linear degradation unreliable on 5–6 of 8 circuits | Documented — reliable on Bahrain and Japan |
| Feature Engineering / Telemetry Analytics 2024-only | Not yet re-run for 2023 |
| 2023 pit loss reuses 2024-derived values | Same tracks; not independently measured |
| Pit loss not filtered for safety-car periods | Saudi Arabia estimate likely inflated |
| WET / INTERMEDIATE thermal model rows are noise | Only 3–18 stints — excluded from outputs |
| Tire cliffs not yet fed into Monte Carlo sim | Detected separately, not in strategy loop |
| No ground-truth backtesting | Future iteration will benchmark vs. real outcomes |

## 🗺️ Roadmap
 
- [x] Scale to full driver grid, 8 races, both 2023 and 2024
- [x] Tire-cliff modeling
- [x] Per-track pit loss estimation
- [x] Thermal (track-temp) degradation model, collinearity diagnosed and fixed via pooling
- [ ] Scale Feature Engineering / Telemetry Analytics to 2023
- [ ] Feed detected tire cliffs and thermal effects back into the Monte Carlo strategy sim
- [ ] Filter pit loss estimation for safety-car periods
- [ ] Backtest predictions against real race outcomes

## 🚀 Setup
 
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

📁 Project Structure

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
│   ├── ingestion/       # FastF1 pulls: telemetry, laps, weather — single/multi-race/multi-year
│   ├── db/              # DuckDB load, merge, and weather-join scripts
│   ├── features/        # corner/brake/throttle/sector/delta detection
│   ├── analytics/       # lap/driver comparison, corner ranking, time loss
│   ├── strategy/        # linear + thermal degradation, tire cliffs, pit loss, Monte Carlo, optimizer
│   └── dashboard/       # HTML dashboard builder, race+year filter
├── notebooks/
└── tests/
```

##💡 Why this project

Background in data analysis, zero prior motorsport domain experience. Built this to learn vehicle dynamics, telemetry analysis, and race strategy hands-on — using real F1 data, not toy datasets.

The thermal degradation work is the clearest demonstration of the approach throughout: build the physically-motivated model, refuse to accept a result that contradicts known physics, diagnose the root cause with a number (|r| = 0.674), and fix it properly with a principled method that recovers the expected physics. A clean-looking wrong result was never an option.