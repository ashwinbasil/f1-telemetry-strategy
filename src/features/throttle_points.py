import duckdb
import pandas as pd
from src.features.corner_detection import detect_corners

DB_PATH = "/app/data/processed/telemetry.duckdb"

def detect_throttle_points(driver="VER", race="Bahrain", year=2024, table="telemetry_multi_year", lookahead_distance=200, throttle_threshold=20):
    corners_df, telemetry_df = detect_corners(driver=driver, race=race, year=year, table=table)

    if len(corners_df) == 0:
        return pd.DataFrame()

    throttle_points = []
    for _, corner in corners_df.iterrows():
        apex_dist = corner["apex_distance"]

        window = telemetry_df[
            (telemetry_df["Distance"] > apex_dist) &
            (telemetry_df["Distance"] <= apex_dist + lookahead_distance)
        ].sort_values("Distance")

        throttling = window[window["Throttle"] >= throttle_threshold]

        if len(throttling) > 0:
            throttle_point_dist = throttling["Distance"].iloc[0]
            throttle_point_speed = throttling["SmoothedSpeed"].iloc[0] if "SmoothedSpeed" in throttling.columns else None
        else:
            throttle_point_dist = None
            throttle_point_speed = None

        throttle_at_apex = telemetry_df.loc[
            (telemetry_df["Distance"] - apex_dist).abs().idxmin(), "Throttle"
        ]

        throttle_points.append({
            "Driver": driver, "Race": race, "Year": year,
            "corner_number": corner["corner_number"],
            "apex_distance": apex_dist,
            "apex_speed": corner["apex_speed"],
            "throttle_at_apex": throttle_at_apex,
            "throttle_point_distance": throttle_point_dist,
            "throttle_point_speed": throttle_point_speed,
            "coasting_length": (throttle_point_dist - apex_dist) if throttle_point_dist is not None else None
        })

    return pd.DataFrame(throttle_points)

def detect_throttle_points_all(drivers=None, table="telemetry_multi_year"):
    con = duckdb.connect(DB_PATH)
    if drivers is None:
        drivers = con.execute(f"SELECT DISTINCT Driver FROM {table}").df()["Driver"].tolist()
    year_race_pairs = con.execute(f"SELECT DISTINCT Year, Race FROM {table}").df()
    con.close()

    all_throttle_points = []
    for _, row in year_race_pairs.iterrows():
        year, race = row["Year"], row["Race"]
        race_count = 0
        for driver in drivers:
            tp_df = detect_throttle_points(driver=driver, race=race, year=year, table=table)
            if len(tp_df) > 0:
                all_throttle_points.append(tp_df)
                race_count += 1
        print(f"{year} {race}: {race_count} drivers processed")

    combined = pd.concat(all_throttle_points, ignore_index=True)
    return combined

if __name__ == "__main__":
    all_throttle_points = detect_throttle_points_all()
    print(f"\nTotal: {len(all_throttle_points)} throttle points across {all_throttle_points['Year'].nunique()} years, {all_throttle_points['Race'].nunique()} races")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE throttle_points_multi_year AS SELECT * FROM all_throttle_points")
    con.close()
    print("Saved throttle_points_multi_year table to DuckDB")
