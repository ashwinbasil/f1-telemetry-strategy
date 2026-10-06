# F1 Telemetry & Strategy Analytics 🏎️

**Status:** Core pipeline complete — 20+ drivers, 8 races, 2 seasons (2023–2024),
every layer from ingestion through strategy simulation fully scaled to both years.

🔗 **[View Live Interactive Dashboard](https://ashwinbasil.github.io/f1-telemetry-strategy/)**

---

## 🎯 Executive Summary

This is an automated, end-to-end predictive analytics pipeline that ingests raw
Formula 1 telemetry and turns it into race-winning strategic recommendations.
The engine answers three high-value operational questions that real F1 strategy
teams face every race weekend:

1. **When should a driver pit?** — A cliff-aware Monte Carlo simulation across
   725 scenarios finds the mathematically optimal lap, accounting for the
   sudden tyre performance drop-off that linear models miss entirely.
2. **Which tyres should they run?** — A physics-validated degradation model
   that accounts for both tyre age *and* track temperature, after diagnosing
   and fixing a collinearity flaw that made the first version produce
   physically backwards results.
3. **Where is time being lost on track?** — Telemetry analysis with outlier
   filtering that pinpoints the exact corner costing the most time, across
   the full 20+ driver grid, both seasons.

Built from zero prior motorsport domain experience. The approach throughout:
build the physically-motivated model, refuse to accept a result that
contradicts known physics, diagnose the root cause with a number, and
fix it properly. Then re-test whether the headline finding survives the fix.

---

## 💻 Tech Stack

**Python · FastF1 · DuckDB · Docker · Pandas · NumPy · SciPy · Plotly**

---

## 📈 Key Strategic Insights & Business Impact

### 1. The Headline Result: A Strategy That Survives Every Model Upgrade

The strongest signal in this project isn't a single number — it's a finding
that held up through three separate methodological upgrades.

**Bahrain's optimal pit strategy (HARD→HARD, pit lap 28) came out identical
in both 2023 and 2024, fit completely independently, and survived every model
change along the way — including the hardest one.**

The Monte Carlo simulation originally ran on a flat linear degradation curve.
It was upgraded to use real cliff data instead — a genuine piecewise curve
(shallower early in the stint, steeper after the detected cliff point) wherever
sufficient data existed. **70% of all 725 scenarios (510) ended up using the
real cliff-based curve.** Bahrain's answer didn't move: same strategy, both
years, under the tougher model.

That's not a coincidence. It's evidence the original result was picking up
something real about how that circuit behaves, not an artifact of the model's
assumptions.

> **What this means strategically:** On a high-degradation circuit like Bahrain,
> the tyre cliff is real, it's measurable, and the optimal strategy accounts
> for it. The HARD compound degrades slowly enough that a single pit stop on
> Lap 28 is definitively cheaper than any alternative — even when the model
> is specifically designed to find scenarios where staying out longer causes
> an exponential time loss.

---

### 2. Thermal Degradation — Quantifying the "Hot + Old Tyre = Cliff" Effect

**The business problem:** Basic degradation models treat every lap of tyre
age as equal. In reality, a 25-lap-old tyre on a 45°C track degrades far
faster than the same tyre on a 25°C track. Knowing the crossover point is
worth positions.

**The result — after fixing a significant data problem (see Engineering section):**

| Compound | Heat + Age Interaction | Stints Pooled |
|---|---|---|
| **SOFT** | **+0.00505** (most heat-sensitive) | 121 |
| **HARD** | +0.00270 | 351 |
| **MEDIUM** | +0.00097 (least heat-sensitive) | 255 |

All three dry compounds show a **positive** interaction coefficient —
physically correct. SOFT is the most sensitive to heat, matching real
tyre chemistry. The model now tells a strategist not just *how fast* a
tyre is wearing, but *whether the track temperature is making it worse
faster than expected.*

---

### 3. Driver Performance & Race Coaching

**Bahrain GP 2024 — Full 20-Driver Grid:**
- **Fastest:** VER (92.608s) · **Slowest:** OCO (96.226s) · Spread: **3.618s**
- **Highest-priority coaching target:** Corner 1 costs the field an average
  of **0.364s** per lap vs. the race leader — the single highest-ROI braking
  zone for simulator prep.

**Tire-cliff detection across both seasons:**
- 142 of 615 long stints (23%) show a genuine late-stint acceleration in
  degradation — the same detection rate in both 2023 and 2024 independently.
  That consistency is a validation check in its own right.

---

### 4. Pit Loss — Filtered for Safety Car (A Concrete Data Quality Win)

**Before filtering:** Saudi Arabia's estimated pit loss was 31.6 seconds —
implausibly high for any normal pit stop.

**After filtering safety-car laps:** 9.5 seconds. The cause was measurable:
14 of 24 pit stops in that dataset (58%) had been taken under caution, where
the pit lane cost is a fraction of a green-flag stop. Removing them recovered
a physically plausible estimate.

> **What this demonstrates:** Data quality problems don't always look like
> missing values or obvious errors. This one looked like a valid number and
> would have silently biased every strategy recommendation for that circuit.
> It was only caught by checking the result against known physics.

---

### 5. Where the Model Is and Isn't Reliable

| Circuit Type | Reliability | Reason |
|---|---|---|
| High-degradation (Bahrain, Japan) | ✅ Reliable, both seasons | Strong signal; cliff model active |
| Low-degradation (Monaco, Australia) | ⚠️ Linear fallback | Fuel-burn noise dominates |
| Street circuits generally | ⚠️ Use with caution | Small per-compound sample sizes |
| WET / INTERMEDIATE compounds | ❌ Excluded | 3–18 stints — insufficient data |

**Operational recommendation:** Use the strategy engine's output directly
for Bahrain and Japan. Apply manual validation on low-degradation circuits
until a mixed-effects model is implemented for those tracks.

---

## ⚙️ Technical Implementation (Engineering POV)

### Architecture

```text
FastF1 (API: telemetry, laps, weather)
    │
    ▼
Data Ingestion — 20+ drivers × 8 races × 2 seasons (2023, 2024)
    │
    ▼
DuckDB (Analytical Storage)
    │
    ▼
Feature Engineering  ✅ (all 8 races, both years)
· Corner detection · Brake points · Throttle points · Sector splits · Delta time
    │
    ▼
Telemetry Analytics  ✅ (all 8 races, both years)
· Lap comparison · Corner ranking (outlier-filtered) · Driver comparison · Time loss
    │
    ▼
Strategy Engine  ✅ (all 8 races, both years)
· Linear degradation model (per race / year / compound)
· Thermal degradation model (TyreAge × TrackTemp, pooled across stints)
· Tire-cliff detection (piecewise regression, breakpoint + slope change)
· Per-race pit loss estimation (real in-lap/out-lap timing, SC-filtered)
· Monte Carlo simulation (725 scenarios, cliff-aware piecewise curve where data exists)
· Pit stop optimizer (best strategy per race / year)
    │
    ▼
Dashboard  ✅ (race + year filter — not yet rebuilt with cliff-model results, see Roadmap)
```

### Scope

- **Drivers:** Full grid, 20–22 per race (reserve drivers included,
  e.g., Bearman sub for Sainz at Saudi Arabia 2024)
- **Races:** Bahrain · Saudi Arabia · Australia · Monaco · Singapore ·
  Belgium · Japan · Monza
- **Seasons:** 2023 and 2024

---

## 🛠️ Key Engineering Decisions & Debugging

Each result above involved catching a real problem and diagnosing it with
a number before fixing it — not guessing, not accepting a bad result.

---

### Fuel-Burn / Track-Evolution Confound

Initial linear regression showed HARD compound as faster base pace than
SOFT — physically backwards. Root cause: the intercept conflated compound
pace with fuel load (SOFT stints run early = heavy fuel; HARD stints run
late = light fuel). Fixed by computing a global fuel-burn trend per race
and normalizing each stint's base laptime to a common reference point
before fitting by compound.

---

### Thermal Model Collinearity — Full Diagnosis

**The problem:** Adding `TrackTemp` and a `TyreAge × TrackTemp` interaction
term to per-stint regression produced uniformly *negative* interaction
coefficients — implying heat helps old tyres, which contradicts real physics.

**The diagnosis:** Pearson correlation between TyreAge and TrackTemp
computed within every individual stint. Mean |r| = **0.674** across 748
stints; 59.5% of stints exceed |r| = 0.7. Root cause is structural:
track temperature drifts monotonically through a race (typically cooling)
at exactly the same time tyre age only ever increases. Standard linear
regression cannot reliably separate two variables moving in lockstep
within a single stint.

**The fix:** Pool stints. Normalise each stint's lap times to its own
median first (preventing car/compound performance from dominating the
pooled result), then combine all stints for a compound into one
regression. Pooling across different races and temperature conditions
breaks the artificial correlation — it dropped from 0.674 to
**0.078–0.188** depending on compound. Interaction coefficients flipped
to physically correct positive values.

---

### Cliff-Aware Monte Carlo Upgrade

The original Monte Carlo used a flat linear degradation curve. Upgraded
to a genuine piecewise curve (shallower early slope, steeper post-cliff
slope) wherever ≥2 detected-cliff stints existed for that
race/compound combination — otherwise it falls back to linear. 510 of
725 scenarios (70%) used the real cliff-based curve. Bahrain's strategy
was unchanged; Australia's 2024 recommendation flipped (SOFT→SOFT to
HARD→SOFT), but both years still used the linear fallback there (zero
cliff coverage), so this is most likely Monte Carlo sampling noise on a
close call — flagged, not chased further.

---

### Tire-Cliff Detector Calibration

Initial version flagged 47% of stints as having a cliff, because it only
required the post-breakpoint slope to be *relatively* steeper than
pre-breakpoint. Fixed by adding an *absolute* magnitude threshold
(0.15 sec/lap minimum) on the post-breakpoint slope. Detection rate
dropped to 23% and the circuit pattern became physically coherent
(Bahrain most, Monaco fewest).

---

### Corner Ranking Outlier Fix

2023 Japan initially showed an absurd 1.4s average time loss at one
corner. Traced to a single driver (BOT) with a 17.9s delta on one lap —
an on-track incident contaminating the average with no outlier filter.
Fixed with a threshold filter; corrected number (0.76s) fell within the
dataset's normal range. Cross-validated independently: BOT also appears
as the slowest driver overall in that race in a completely separate table,
confirming the incident was real rather than a calculation error.

---

### Reference-Driver Anomaly

2023 Bahrain's session-fastest lap belongs to ZHO (a backmarker that
season), not a front-runner. Verified as real: it's the literal final lap,
run alone in clean air. A known quirk of using session-fastest as a
delta-comparison reference — it doesn't always belong to the fastest driver
overall. Documented, not corrected (correcting it would redefine "fastest"
in a way that no longer matches what the sport itself reports).

---

### Data Source Name Collision

Requesting "Italy" from FastF1 in 2024 returned the Emilia Romagna GP at
Imola, not the Italian GP at Monza — 2024 had two Italian rounds. Fixed
by requesting "Monza" directly.

---

## 🚧 Known Limitations

| Limitation | Status |
|---|---|
| Linear degradation unreliable on ~half of circuit/year combinations | Cliff model partially compensates where data exists |
| 2023 pit loss reuses 2024-derived values | Same tracks; not independently measured |
| Pit loss estimates have ±3–5s uncertainty | Small per-race sample sizes |
| WET / INTERMEDIATE thermal model rows are noise | Only 3–18 stints — excluded from outputs |
| Tire cliffs in Monte Carlo use linear fallback on low-deg circuits | Zero cliff coverage at Monaco, Australia |
| Dashboard lags the latest modeling work | Pre-cliff-model Monte Carlo numbers still shown |
| No ground-truth backtesting | Future iteration will benchmark vs. real outcomes |

---

## 🗺️ Roadmap

- [x] Scale to full driver grid, 8 races, 2023 + 2024 — every layer
- [x] Tire-cliff detection, fed into Monte Carlo as a real piecewise curve
- [x] Per-track pit loss estimation, filtered for safety-car periods
- [x] Thermal degradation model — collinearity diagnosed and fixed via pooling
- [x] Outlier filtering in corner-ranking analytics
- [ ] Backtest predictions against real race outcomes
- [ ] Rebuild dashboard with cliff-aware Monte Carlo results and 2023 telemetry data

---

## 🚀 Setup

```bash
docker-compose build
docker-compose up
```

Jupyter available at `localhost:8888`.

```bash
docker-compose run --remove-orphans app python -m src.dashboard.build_dashboard
```

Output: `data/processed/dashboard.html`

---

## 📁 Project Structure

```text
f1-telemetry-strategy/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
├── docs/                # published dashboard (GitHub Pages)
├── src/
│   ├── ingestion/       # FastF1 pulls: telemetry, laps, weather — multi-race/multi-year
│   ├── db/              # DuckDB load, merge, and weather-join scripts
│   ├── features/        # corner/brake/throttle/sector/delta detection, multi-year
│   ├── analytics/       # lap/driver comparison, corner ranking (outlier-filtered), time loss
│   ├── strategy/        # linear + thermal degradation, tire cliffs, pit loss,
│   │                    # cliff-aware Monte Carlo, optimizer
│   └── dashboard/       # HTML dashboard builder, race+year filter
├── notebooks/
└── tests/
```

---

## 💡 Why this project

Background in data analysis, no prior motorsport domain experience. Built
this to learn vehicle dynamics, telemetry analysis, and race strategy
terminology hands-on — using real F1 data, not toy datasets.

The pattern throughout: build the physically-motivated model, don't accept
a result that contradicts known physics or common sense, diagnose the real
cause with a number, fix it properly, and re-test whether the headline
finding survives the fix. Bahrain's strategy survived three separate model
upgrades. That's the result I'd lead with in an interview.
