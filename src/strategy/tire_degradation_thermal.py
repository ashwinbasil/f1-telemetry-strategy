import duckdb
import pandas as pd
import numpy as np

DB_PATH = "/app/data/processed/telemetry.duckdb"

def load_stint_data():
    con = duckdb.connect(DB_PATH)
    df = con.execute("""
        SELECT Driver, Race, Year, Stint, LapNumber, LapTime_sec, Compound, TyreLife, TrackTemp
        FROM sector_splits_with_weather
        WHERE LapTime_sec IS NOT NULL AND Compound IS NOT NULL AND TyreLife IS NOT NULL
          AND TrackTemp IS NOT NULL
        ORDER BY Race, Year, Driver, Stint, TyreLife
    """).df()
    con.close()
    return df

def compute_global_trend(df):
    median = df["LapTime_sec"].median()
    clean = df[df["LapTime_sec"] < median + 3]
    slope, intercept = np.polyfit(clean["LapNumber"], clean["LapTime_sec"], 1)
    return slope

def fit_thermal_model(x_age, x_temp, y):
    # multiple linear regression: y = b0 + b1*age + b2*temp + b3*(age*temp)
    # interaction term captures the "hot AND old" compounding cliff effect
    interaction = x_age * x_temp
    X = np.column_stack([np.ones(len(x_age)), x_age, x_temp, interaction])
    coeffs, residuals, rank, sv = np.linalg.lstsq(X, y, rcond=None)
    return coeffs  # [intercept, age_coef, temp_coef, interaction_coef]

def fit_degradation(df, min_laps=5):
    results = []
    for (year, race), group in df.groupby(["Year", "Race"]):
        global_trend_slope = compute_global_trend(group)

        for (driver, stint), stint_group in group.groupby(["Driver", "Stint"]):
            if len(stint_group) < min_laps:
                continue

            compound = stint_group["Compound"].iloc[0]
            x_age = stint_group["TyreLife"].values.astype(float)
            x_temp = stint_group["TrackTemp"].values.astype(float)
            y = stint_group["LapTime_sec"].values
            avg_lap_number = stint_group["LapNumber"].mean()
            avg_temp = x_temp.mean()

            median = np.median(y)
            mask = y < median + 3
            x_age, x_temp, y = x_age[mask], x_temp[mask], y[mask]

            if len(x_age) < min_laps or x_temp.std() < 0.1:
                # need some temp variation within stint to fit interaction meaningfully;
                # if track temp barely moved during this stint, fall back to age-only slope
                if len(x_age) >= min_laps:
                    slope, intercept = np.polyfit(x_age, y, 1)
                    results.append({
                        "Year": year, "Race": race, "Driver": driver, "Stint": stint,
                        "Compound": compound, "laps_in_stint": len(x_age),
                        "avg_track_temp": round(avg_temp, 1),
                        "age_coef": round(slope, 4), "temp_coef": None, "interaction_coef": None,
                        "model_type": "linear_fallback_no_temp_variation"
                    })
                continue

            coeffs = fit_thermal_model(x_age, x_temp, y)
            intercept, age_coef, temp_coef, interaction_coef = coeffs
            normalized_base = intercept - (global_trend_slope * avg_lap_number)

            results.append({
                "Year": year, "Race": race, "Driver": driver, "Stint": stint,
                "Compound": compound, "laps_in_stint": len(x_age),
                "avg_track_temp": round(avg_temp, 1),
                "age_coef": round(age_coef, 4),
                "temp_coef": round(temp_coef, 4),
                "interaction_coef": round(interaction_coef, 5),
                "base_laptime_normalized": round(normalized_base, 3),
                "model_type": "thermal"
            })

    return pd.DataFrame(results)

if __name__ == "__main__":
    df = load_stint_data()
    print(f"Loaded {len(df)} laps with temp data")

    results = fit_degradation(df)
    thermal = results[results["model_type"] == "thermal"]
    fallback = results[results["model_type"] == "linear_fallback_no_temp_variation"]
    print(f"Fitted thermal model on {len(thermal)} stints, fell back to age-only on {len(fallback)} (insufficient temp variation within stint)")

    print("\nInteraction coefficient by compound (positive = hot+old compounds harder):")
    print(thermal.groupby("Compound")["interaction_coef"].agg(["mean", "count"]).round(5).to_string())

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE tire_degradation_thermal AS SELECT * FROM results")
    con.close()
    print("\nSaved tire_degradation_thermal table to DuckDB")
def check_collinearity(df):
    con = duckdb.connect(DB_PATH)
    df2 = con.execute("""
        SELECT Driver, Race, Year, Stint, TyreLife, TrackTemp
        FROM sector_splits_with_weather
        WHERE TyreLife IS NOT NULL AND TrackTemp IS NOT NULL
    """).df()
    con.close()

    corrs = []
    for (race, year, driver, stint), group in df2.groupby(["Race", "Year", "Driver", "Stint"]):
        if len(group) < 5:
            continue
        corr = group["TyreLife"].corr(group["TrackTemp"])
        corrs.append(corr)

    import numpy as np
    corrs = np.array(corrs)
    print(f"\nWithin-stint TyreLife vs TrackTemp correlation across {len(corrs)} stints:")
    print(f"  Mean |correlation|: {np.abs(corrs).mean():.3f}")
    print(f"  Fraction with |corr| > 0.7: {(np.abs(corrs) > 0.7).mean():.1%}")
