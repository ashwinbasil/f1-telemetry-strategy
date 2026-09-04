import duckdb
import numpy as np
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def time_to_seconds(t):
    return pd.to_timedelta(t).total_seconds()

def find_session_fastest(table="telemetry_all"):
    con = duckdb.connect(DB_PATH)
    df = con.execute(f"""
        SELECT Driver, MAX(LapNumber) as LapNumber, MAX(Distance) as MaxDist
        FROM {table}
        GROUP BY Driver
    """).df()
    con.close()
    # fastest lap = lap with lowest max Time value at end of lap, approximate via laps table instead
    con = duckdb.connect(DB_PATH)
    laps = con.execute("""
        SELECT Driver, LapTime_sec
        FROM sector_splits
        WHERE LapTime_sec IS NOT NULL
        ORDER BY LapTime_sec ASC
        LIMIT 1
    """).df()
    con.close()
    return laps["Driver"].iloc[0], laps["LapTime_sec"].iloc[0]

def compute_delta_vs_reference(driver, reference_driver, table="telemetry_all"):
    con = duckdb.connect(DB_PATH)
    df_driver = con.execute(f"SELECT Distance, Time, Speed FROM {table} WHERE Driver = '{driver}' ORDER BY Distance").df()
    df_ref = con.execute(f"SELECT Distance, Time, Speed FROM {table} WHERE Driver = '{reference_driver}' ORDER BY Distance").df()
    con.close()

    df_driver = df_driver.dropna(subset=["Distance"]).drop_duplicates(subset=["Distance"])
    df_ref = df_ref.dropna(subset=["Distance"]).drop_duplicates(subset=["Distance"])

    df_driver["Time_sec"] = df_driver["Time"].apply(time_to_seconds)
    df_ref["Time_sec"] = df_ref["Time"].apply(time_to_seconds)

    common_distance = np.linspace(
        max(df_driver["Distance"].min(), df_ref["Distance"].min()),
        min(df_driver["Distance"].max(), df_ref["Distance"].max()),
        500
    )

    time_driver = np.interp(common_distance, df_driver["Distance"], df_driver["Time_sec"])
    time_ref = np.interp(common_distance, df_ref["Distance"], df_ref["Time_sec"])

    delta = time_driver - time_ref  # positive = driver slower than reference

    result = pd.DataFrame({
        "Driver": driver,
        "Reference": reference_driver,
        "Distance": common_distance,
        "Delta": delta
    })
    return result

def compute_all_deltas(table="telemetry_all"):
    reference_driver, ref_laptime = find_session_fastest(table)
    print(f"Session fastest: {reference_driver} ({ref_laptime:.3f}s), using as reference\n")

    con = duckdb.connect(DB_PATH)
    drivers = con.execute(f"SELECT DISTINCT Driver FROM {table}").df()["Driver"].tolist()
    con.close()

    all_deltas = []
    for driver in drivers:
        if driver == reference_driver:
            continue
        try:
            delta_df = compute_delta_vs_reference(driver, reference_driver, table)
            final_delta = delta_df["Delta"].iloc[-1]
            print(f"{driver}: {final_delta:+.3f}s vs {reference_driver}")
            all_deltas.append(delta_df)
        except Exception as e:
            print(f"Failed {driver}: {e}")

    combined = pd.concat(all_deltas, ignore_index=True)
    return combined, reference_driver

if __name__ == "__main__":
    combined, reference_driver = compute_all_deltas()
    print(f"\nTotal delta rows: {len(combined)}, reference driver: {reference_driver}")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE delta_vs_fastest AS SELECT * FROM combined")
    con.close()
    print("Saved delta_vs_fastest table to DuckDB")