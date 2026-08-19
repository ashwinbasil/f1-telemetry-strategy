import duckdb
import pandas as pd
import numpy as np

DB_PATH = "/app/data/processed/telemetry.duckdb"

def load_stint_data(driver=None):
    con = duckdb.connect(DB_PATH)
    query = """
        SELECT Driver, Stint, LapNumber, LapTime_sec, Compound, TyreLife
        FROM sector_splits
        WHERE LapTime_sec IS NOT NULL
          AND Compound IS NOT NULL
          AND TyreLife IS NOT NULL
    """
    if driver:
        query += f" AND Driver = '{driver}'"
    query += " ORDER BY Driver, Stint, TyreLife"

    df = con.execute(query).df()
    con.close()
    return df

def compute_global_trend(df):
    # strip outlier laps (pit in/out, safety car) before fitting global trend
    median = df["LapTime_sec"].median()
    clean = df[df["LapTime_sec"] < median + 3]
    slope, intercept = np.polyfit(clean["LapNumber"], clean["LapTime_sec"], 1)
    return slope  # sec/lap, combined fuel burn + track evolution effect

def fit_degradation(df, min_laps=5):
    global_trend_slope = compute_global_trend(df)

    results = []
    for (driver, stint), group in df.groupby(["Driver", "Stint"]):
        if len(group) < min_laps:
            continue

        compound = group["Compound"].iloc[0]
        x = group["TyreLife"].values
        y = group["LapTime_sec"].values
        avg_lap_number = group["LapNumber"].mean()

        median = np.median(y)
        mask = y < median + 3
        x, y = x[mask], y[mask]

        if len(x) < min_laps:
            continue

        slope, intercept = np.polyfit(x, y, 1)

        # normalize base_laptime to lap-0 reference, strip global fuel/evolution trend
        normalized_base = intercept - (global_trend_slope * avg_lap_number)

        results.append({
            "Driver": driver,
            "Stint": stint,
            "Compound": compound,
            "laps_in_stint": len(x),
            "avg_lap_number": round(avg_lap_number, 1),
            "deg_rate_sec_per_lap": round(slope, 4),
            "base_laptime_raw": round(intercept, 3),
            "base_laptime_normalized": round(normalized_base, 3)
        })

    return pd.DataFrame(results), global_trend_slope

if __name__ == "__main__":
    df = load_stint_data()
    deg_results, global_trend = fit_degradation(df)
    deg_results = deg_results.sort_values(["Compound", "deg_rate_sec_per_lap"])

    print(f"Global fuel/track-evolution trend: {global_trend:.4f} sec/lap\n")
    print("Tire degradation by stint:")
    print(deg_results.to_string(index=False))

    print("\nAverage deg rate + normalized base laptime by compound:")
    print(deg_results.groupby("Compound")[["deg_rate_sec_per_lap", "base_laptime_normalized"]].mean().round(4).to_string())

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE tire_degradation AS SELECT * FROM deg_results")
    con.close()
    print("\nSaved tire_degradation table to DuckDB")