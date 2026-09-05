import duckdb
import pandas as pd
import numpy as np

DB_PATH = "/app/data/processed/telemetry.duckdb"

def load_stint_data(table="sector_splits_multi_race", driver=None, race=None):
    con = duckdb.connect(DB_PATH)
    query = f"""
        SELECT Driver, Race, Year, Stint, LapNumber, LapTime_sec, Compound, TyreLife
        FROM {table}
        WHERE LapTime_sec IS NOT NULL
          AND Compound IS NOT NULL
          AND TyreLife IS NOT NULL
    """
    if driver:
        query += f" AND Driver = '{driver}'"
    if race:
        query += f" AND Race = '{race}'"
    query += " ORDER BY Race, Driver, Stint, TyreLife"

    df = con.execute(query).df()
    con.close()
    return df

def compute_global_trend(df):
    median = df["LapTime_sec"].median()
    clean = df[df["LapTime_sec"] < median + 3]
    slope, intercept = np.polyfit(clean["LapNumber"], clean["LapTime_sec"], 1)
    return slope

def fit_degradation(df, min_laps=5):
    results = []
    for race, race_group in df.groupby("Race"):
        global_trend_slope = compute_global_trend(race_group)

        for (driver, stint), group in race_group.groupby(["Driver", "Stint"]):
            if len(group) < min_laps:
                continue

            compound = group["Compound"].iloc[0]
            year = group["Year"].iloc[0]
            x = group["TyreLife"].values
            y = group["LapTime_sec"].values
            avg_lap_number = group["LapNumber"].mean()

            median = np.median(y)
            mask = y < median + 3
            x, y = x[mask], y[mask]

            if len(x) < min_laps:
                continue

            slope, intercept = np.polyfit(x, y, 1)
            normalized_base = intercept - (global_trend_slope * avg_lap_number)

            results.append({
                "Race": race,
                "Year": year,
                "Driver": driver,
                "Stint": stint,
                "Compound": compound,
                "laps_in_stint": len(x),
                "deg_rate_sec_per_lap": round(slope, 4),
                "base_laptime_normalized": round(normalized_base, 3)
            })

    return pd.DataFrame(results)

if __name__ == "__main__":
    df = load_stint_data()
    deg_results = fit_degradation(df)
    deg_results = deg_results.sort_values(["Race", "Compound", "deg_rate_sec_per_lap"])

    print(f"Tire degradation, multi-race, {deg_results['Race'].nunique()} races:")
    print(deg_results.groupby(["Race", "Compound"])[["deg_rate_sec_per_lap", "base_laptime_normalized"]].mean().round(4).to_string())

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE tire_degradation_multi_race AS SELECT * FROM deg_results")
    con.close()
    print("\nSaved tire_degradation_multi_race table to DuckDB")