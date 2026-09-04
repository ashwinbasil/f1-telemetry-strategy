import duckdb
import pandas as pd
from src.features.corner_detection import detect_corners

DB_PATH = "/app/data/processed/telemetry.duckdb"

def detect_brake_points(driver="VER", table="telemetry_all", lookback_distance=200):
    corners_df, telemetry_df = detect_corners(driver=driver, table=table)

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
            "corner_number": corner["corner_number"],
            "apex_distance": apex_dist,
            "apex_speed": corner["apex_speed"],
            "brake_point_distance": brake_point_dist,
            "brake_point_speed": brake_point_speed,
            "brake_zone_length": (apex_dist - brake_point_dist) if brake_point_dist is not None else None
        })

    return pd.DataFrame(brake_points)

def detect_brake_points_all_drivers(drivers=None, table="telemetry_all"):
    con = duckdb.connect(DB_PATH)
    if drivers is None:
        drivers = con.execute(f"SELECT DISTINCT Driver FROM {table}").df()["Driver"].tolist()
    con.close()

    all_brake_points = []
    for driver in drivers:
        bp_df = detect_brake_points(driver=driver, table=table)
        if len(bp_df) > 0:
            all_brake_points.append(bp_df)
        print(f"{driver}: {len(bp_df)} brake points")

    combined = pd.concat(all_brake_points, ignore_index=True)
    return combined

if __name__ == "__main__":
    all_brake_points = detect_brake_points_all_drivers()
    print(f"\nTotal: {len(all_brake_points)} brake points across {all_brake_points['Driver'].nunique()} drivers")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE brake_points_all AS SELECT * FROM all_brake_points")
    con.close()
    print("Saved brake_points_all table to DuckDB")