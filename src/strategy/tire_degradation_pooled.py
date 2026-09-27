import duckdb
import pandas as pd
import numpy as np

DB_PATH = "/app/data/processed/telemetry.duckdb"

def load_pooled_data():
    con = duckdb.connect(DB_PATH)
    df = con.execute("""
        SELECT Driver, Race, Year, Stint, LapNumber, LapTime_sec, Compound, TyreLife, TrackTemp
        FROM sector_splits_with_weather
        WHERE LapTime_sec IS NOT NULL AND Compound IS NOT NULL
          AND TyreLife IS NOT NULL AND TrackTemp IS NOT NULL
    """).df()
    con.close()
    return df

def fit_pooled_thermal(df, compound, min_stint_laps=5):
    sub = df[df["Compound"] == compound].copy()

    # normalize each stint's laptime to strip fuel/track-evolution + driver/car pace baseline,
    # so pooling doesn't just pick up "which driver/stint is fast" as noise
    normalized_rows = []
    for (race, year, driver, stint), group in sub.groupby(["Race", "Year", "Driver", "Stint"]):
        if len(group) < min_stint_laps:
            continue
        baseline = group["LapTime_sec"].median()
        g = group.copy()
        g["LapTime_delta"] = g["LapTime_sec"] - baseline
        normalized_rows.append(g)

    if not normalized_rows:
        return None

    pooled = pd.concat(normalized_rows, ignore_index=True)

    # check pooled collinearity, this is the number that matters
    pooled_corr = pooled["TyreLife"].corr(pooled["TrackTemp"])

    x_age = pooled["TyreLife"].values.astype(float)
    x_temp = pooled["TrackTemp"].values.astype(float)
    y = pooled["LapTime_delta"].values
    interaction = x_age * x_temp

    X = np.column_stack([np.ones(len(x_age)), x_age, x_temp, interaction])
    coeffs, residuals, rank, sv = np.linalg.lstsq(X, y, rcond=None)

    return {
        "compound": compound,
        "n_laps_pooled": len(pooled),
        "n_stints_pooled": len(normalized_rows),
        "pooled_corr_age_temp": round(pooled_corr, 3),
        "age_coef": round(coeffs[1], 4),
        "temp_coef": round(coeffs[2], 4),
        "interaction_coef": round(coeffs[3], 5)
    }

if __name__ == "__main__":
    df = load_pooled_data()
    compounds = df["Compound"].unique()

    results = []
    for compound in compounds:
        r = fit_pooled_thermal(df, compound)
        if r:
            results.append(r)

    results_df = pd.DataFrame(results)
    print("Pooled thermal degradation model (age + temp + interaction, laptime normalized per stint):")
    print(results_df.to_string(index=False))

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE tire_degradation_pooled_thermal AS SELECT * FROM results_df")
    con.close()
    print("\nSaved tire_degradation_pooled_thermal table to DuckDB")