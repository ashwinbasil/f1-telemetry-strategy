import duckdb
import pandas as pd
import numpy as np

DB_PATH = "/app/data/processed/telemetry.duckdb"

def time_to_seconds(t):
    if pd.isna(t):
        return None
    try:
        return pd.to_timedelta(t).total_seconds()
    except:
        return None

def estimate_pit_loss(green_flag_only=True):
    con = duckdb.connect(DB_PATH)
    df = con.execute("""
        SELECT Driver, Race, LapNumber, LapTime, PitInTime, PitOutTime, TrackStatus
        FROM laps_multi_race
        WHERE LapTime IS NOT NULL
    """).df()
    con.close()

    df["LapTime_sec"] = df["LapTime"].apply(time_to_seconds)
    df = df.dropna(subset=["LapTime_sec"])
    df["TrackStatus"] = df["TrackStatus"].astype(str)

    results = []
    for race, race_group in df.groupby("Race"):
        normal_pace = race_group[
            race_group["PitInTime"].isna() & race_group["PitOutTime"].isna()
        ]["LapTime_sec"].median()

        pit_laps = race_group[race_group["PitInTime"].notna() | race_group["PitOutTime"].notna()]

        if green_flag_only:
            pit_laps_filtered = pit_laps[pit_laps["TrackStatus"] == "1"]
        else:
            pit_laps_filtered = pit_laps

        pit_lap_times = pit_laps_filtered["LapTime_sec"].dropna()
        n_excluded = len(pit_laps) - len(pit_laps_filtered)

        if len(pit_lap_times) < 3 or pd.isna(normal_pace):
            print(f"  {race}: skipped, only {len(pit_lap_times)} green-flag pit laps available")
            continue

        median_pit_lap_time = pit_lap_times.median()
        pit_loss_estimate = median_pit_lap_time - normal_pace

        results.append({
            "Race": race,
            "normal_pace_sec": round(normal_pace, 3),
            "median_pit_lap_time_sec": round(median_pit_lap_time, 3),
            "pit_loss_estimate_sec": round(pit_loss_estimate, 2),
            "n_pit_laps_sampled": len(pit_lap_times),
            "n_pit_laps_excluded_non_green": n_excluded
        })

    return pd.DataFrame(results)

if __name__ == "__main__":
    print("Estimated pit loss per race (green-flag laps only):")
    pit_loss_df = estimate_pit_loss(green_flag_only=True)
    print(pit_loss_df.to_string(index=False))

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE pit_loss_estimates AS SELECT * FROM pit_loss_df")
    con.close()
    print("\nSaved pit_loss_estimates table to DuckDB")