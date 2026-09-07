import duckdb
import pandas as pd
from src.features.corner_detection import detect_corners

DB_PATH = "/app/data/processed/telemetry.duckdb"

def detect_brake_points(driver="VER", race="Bahrain", table="telemetry_multi_race", lookback_distance=200):
    corners_df, telemetry_df = detect_corners(driver=driver, race=race, table=table)

    if len(corners_df) == 0:
        return pd.DataFrame()

    brake_points = []
    for _, corner in corners_df.iterrows():
        apex_dist = corner["apex_distance"]

        window = telemetry_df[
            (telemetry_df["Distance"] >= apex_dist - lookback_distance) &
            (telemetry_df["Distance"] <= apex_dist)
        ].sort_values("Distance")

        braking = window[window["Brake"] == True]

        if len(braking) > 0:
            brake_point_dist = braking["Distance"].iloc[0]
            brake_point_speed = braking["SmoothedSpeed"].iloc[0] if "SmoothedSpeed" in braking.columns else None
        else:
            brake_point_dist = None
            brake_point_speed = None

        brake_points.append({
            "Driver": driver,
            "Race": race,
            "corner_number": corner["corner_number"],
            "apex_distance": apex_dist,
            "apex_speed": corner["apex_speed"],
            "brake_point_distance": brake_point_dist,
            "brake_point_speed": brake_point_speed,
            "brake_zone_length": (apex_dist - brake_point_dist) if brake_point_dist is not None else None
        })

    return pd.DataFrame(brake_points)

def detect_brake_points_all(drivers=None, races=None, table="telemetry_multi_race"):
    con = duckdb.connect(DB_PATH)
    if drivers is None:
        drivers = con.execute(f"SELECT DISTINCT Driver FROM {table}").df()["Driver"].tolist()
    if races is None:
        races = con.execute(f"SELECT DISTINCT Race FROM {table}").df()["Race"].tolist()
    con.close()

    all_brake_points = []
    for race in races:
        race_count = 0
        for driver in drivers:
            bp_df = detect_brake_points(driver=driver, race=race, table=table)
            if len(bp_df) > 0:
                all_brake_points.append(bp_df)
                race_count += 1
        print(f"{race}: {race_count} drivers processed")

    combined = pd.concat(all_brake_points, ignore_index=True)
    return combined

if __name__ == "__main__":
    all_brake_points = detect_brake_points_all()
    print(f"\nTotal: {len(all_brake_points)} brake points across {all_brake_points['Race'].nunique()} races, {all_brake_points['Driver'].nunique()} drivers")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE brake_points_multi_race AS SELECT * FROM all_brake_points")
    con.close()
    print("Saved brake_points_multi_race table to DuckDB")