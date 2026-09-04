import duckdb
import pandas as pd
from src.features.corner_detection import detect_corners

DB_PATH = "/app/data/processed/telemetry.duckdb"

def detect_throttle_points(driver="VER", table="telemetry_all", lookahead_distance=200, throttle_threshold=20):
    corners_df, telemetry_df = detect_corners(driver=driver, table=table)

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
            "Driver": driver,
            "corner_number": corner["corner_number"],
            "apex_distance": apex_dist,
            "apex_speed": corner["apex_speed"],
            "throttle_at_apex": throttle_at_apex,
            "throttle_point_distance": throttle_point_dist,
            "throttle_point_speed": throttle_point_speed,
            "coasting_length": (throttle_point_dist - apex_dist) if throttle_point_dist is not None else None
        })

    return pd.DataFrame(throttle_points)

def detect_throttle_points_all_drivers(drivers=None, table="telemetry_all"):
    con = duckdb.connect(DB_PATH)
    if drivers is None:
        drivers = con.execute(f"SELECT DISTINCT Driver FROM {table}").df()["Driver"].tolist()
    con.close()

    all_throttle_points = []
    for driver in drivers:
        tp_df = detect_throttle_points(driver=driver, table=table)
        if len(tp_df) > 0:
            all_throttle_points.append(tp_df)
        print(f"{driver}: {len(tp_df)} throttle points")

    combined = pd.concat(all_throttle_points, ignore_index=True)
    return combined

if __name__ == "__main__":
    all_throttle_points = detect_throttle_points_all_drivers()
    print(f"\nTotal: {len(all_throttle_points)} throttle points across {all_throttle_points['Driver'].nunique()} drivers")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE throttle_points_all AS SELECT * FROM all_throttle_points")
    con.close()
    print("Saved throttle_points_all table to DuckDB")
