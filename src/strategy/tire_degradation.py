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

def fit_degradation(df, min_laps=5):
    results = []
    for (driver, stint), group in df.groupby(["Driver", "Stint"]):
        if len(group) < min_laps:
            continue

        compound = group["Compound"].iloc[0]
        x = group["TyreLife"].values
        y = group["LapTime_sec"].values

        # filter outliers: laps way slower than stint median (safety car, traffic, pit in/out laps)
        median = np.median(y)
        mask = y < median + 3
        x, y = x[mask], y[mask]

        if len(x) < min_laps:
            continue

        slope, intercept = np.polyfit(x, y, 1)

        results.append({
            "Driver": driver,
            "Stint": stint,
            "Compound": compound,
            "laps_in_stint": len(x),
            "deg_rate_sec_per_lap": round(slope, 4),
            "base_laptime": round(intercept, 3)
        })

    return pd.DataFrame(results)

if __name__ == "__main__":
    df = load_stint_data()
    deg_results = fit_degradation(df)
    deg_results = deg_results.sort_values(["Compound", "deg_rate_sec_per_lap"])
    print("Tire degradation by stint:")
    print(deg_results.to_string(index=False))

    print("\nAverage deg rate by compound:")
    print(deg_results.groupby("Compound")["deg_rate_sec_per_lap"].mean().round(4).to_string())

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE tire_degradation AS SELECT * FROM deg_results")
    con.close()
    print("\nSaved tire_degradation table to DuckDB")
