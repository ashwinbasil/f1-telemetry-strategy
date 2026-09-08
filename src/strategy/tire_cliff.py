import duckdb
import pandas as pd
import numpy as np

DB_PATH = "/app/data/processed/telemetry.duckdb"

def load_long_stints(min_laps=10):
    con = duckdb.connect(DB_PATH)
    df = con.execute("""
        SELECT Driver, Race, Stint, LapNumber, LapTime_sec, Compound, TyreLife
        FROM sector_splits_multi_race
        WHERE LapTime_sec IS NOT NULL AND Compound IS NOT NULL AND TyreLife IS NOT NULL
        ORDER BY Race, Driver, Stint, TyreLife
    """).df()
    con.close()
    return df

def fit_piecewise(x, y, min_segment=4):
    n = len(x)
    best_sse = np.inf
    best_breakpoint = None
    best_slopes = None

    for bp_idx in range(min_segment, n - min_segment):
        x1, y1 = x[:bp_idx], y[:bp_idx]
        x2, y2 = x[bp_idx:], y[bp_idx:]

        slope1, intercept1 = np.polyfit(x1, y1, 1)
        slope2, intercept2 = np.polyfit(x2, y2, 1)

        pred1 = slope1 * x1 + intercept1
        pred2 = slope2 * x2 + intercept2
        sse = np.sum((y1 - pred1) ** 2) + np.sum((y2 - pred2) ** 2)

        if sse < best_sse:
            best_sse = sse
            best_breakpoint = x[bp_idx]
            best_slopes = (slope1, slope2)

    return best_breakpoint, best_slopes

def detect_cliffs(df, min_laps=10, cliff_ratio_threshold=1.5, min_cliff_slope=0.15):
    results = []
    for (race, driver, stint), group in df.groupby(["Race", "Driver", "Stint"]):
        if len(group) < min_laps:
            continue

        compound = group["Compound"].iloc[0]
        x = group["TyreLife"].values
        y = group["LapTime_sec"].values

        median = np.median(y)
        mask = y < median + 3
        x, y = x[mask], y[mask]

        if len(x) < min_laps:
            continue

        overall_slope, _ = np.polyfit(x, y, 1)
        breakpoint, slopes = fit_piecewise(x, y)

        if breakpoint is None:
            continue

        slope_before, slope_after = slopes
        # real cliff: post-break slope must be clearly steep in absolute terms, not just relatively steeper
        cliff_detected = (slope_after >= min_cliff_slope) and (slope_after >= slope_before + min_cliff_slope)

        results.append({
            "Race": race,
            "Driver": driver,
            "Stint": stint,
            "Compound": compound,
            "laps_in_stint": len(x),
            "overall_linear_slope": round(overall_slope, 4),
            "cliff_tyre_age": round(breakpoint, 1),
            "slope_before_cliff": round(slope_before, 4),
            "slope_after_cliff": round(slope_after, 4),
            "cliff_detected": cliff_detected
        })

    return pd.DataFrame(results)

if __name__ == "__main__":
    df = load_long_stints()
    print(f"Loaded {len(df)} laps for cliff analysis")

    cliff_results = detect_cliffs(df)
    print(f"\nAnalyzed {len(cliff_results)} long stints (10+ laps)")

    cliffs_found = cliff_results[cliff_results["cliff_detected"] == True]
    print(f"Cliffs detected: {len(cliffs_found)} of {len(cliff_results)} stints")

    print("\nStints with detected cliffs:")
    print(cliffs_found[["Race", "Driver", "Stint", "Compound", "laps_in_stint", "cliff_tyre_age", "slope_before_cliff", "slope_after_cliff"]].to_string(index=False))

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE tire_cliff_analysis AS SELECT * FROM cliff_results")
    con.close()
    print("\nSaved tire_cliff_analysis table to DuckDB")