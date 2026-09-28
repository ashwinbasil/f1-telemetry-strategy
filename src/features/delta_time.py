import duckdb
import numpy as np
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def time_to_seconds(t):
    return pd.to_timedelta(t).total_seconds()

def find_fastest(race, year):
    con = duckdb.connect(DB_PATH)
    laps = con.execute(f"""
        SELECT Driver, LapTime_sec FROM sector_splits_multi_year
        WHERE Race = '{race}' AND Year = {year} AND LapTime_sec IS NOT NULL
        ORDER BY LapTime_sec ASC LIMIT 1
    """).df()
    con.close()
    return laps["Driver"].iloc[0], laps["LapTime_sec"].iloc[0]

def compute_delta_vs_reference(driver, race, year, reference_driver, table="telemetry_multi_year"):
    con = duckdb.connect(DB_PATH)
    df_driver = con.execute(f"SELECT Distance, Time, Speed FROM {table} WHERE Driver = '{driver}' AND Race = '{race}' AND Year = {year} ORDER BY Distance").df()
    df_ref = con.execute(f"SELECT Distance, Time, Speed FROM {table} WHERE Driver = '{reference_driver}' AND Race = '{race}' AND Year = {year} ORDER BY Distance").df()
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
    delta = time_driver - time_ref

    return pd.DataFrame({"Driver": driver, "Race": race, "Year": year, "Reference": reference_driver, "Distance": common_distance, "Delta": delta})

def compute_all(table="telemetry_multi_year"):
    con = duckdb.connect(DB_PATH)
    year_race_pairs = con.execute(f"SELECT DISTINCT Year, Race FROM {table}").df()
    con.close()

    all_deltas = []
    for _, row in year_race_pairs.iterrows():
        year, race = row["Year"], row["Race"]
        reference_driver, ref_laptime = find_fastest(race, year)

        con = duckdb.connect(DB_PATH)
        drivers = con.execute(f"SELECT DISTINCT Driver FROM {table} WHERE Race = '{race}' AND Year = {year}").df()["Driver"].tolist()
        con.close()

        count = 0
        for driver in drivers:
            if driver == reference_driver:
                continue
            try:
                delta_df = compute_delta_vs_reference(driver, race, year, reference_driver, table)
                all_deltas.append(delta_df)
                count += 1
            except Exception as e:
                print(f"  {year} {race} {driver}: failed ({e})")
        print(f"{year} {race}: fastest={reference_driver} ({ref_laptime:.3f}s), {count} drivers compared")

    combined = pd.concat(all_deltas, ignore_index=True)
    return combined

if __name__ == "__main__":
    combined = compute_all()
    print(f"\nTotal delta rows: {len(combined)} across {combined['Year'].nunique()} years, {combined['Race'].nunique()} races")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE delta_vs_fastest_multi_year AS SELECT * FROM combined")
    con.close()
    print("Saved delta_vs_fastest_multi_year table to DuckDB")