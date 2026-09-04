import duckdb
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter, argrelextrema

DB_PATH = "/app/data/processed/telemetry.duckdb"

def detect_corners(driver="VER", table="telemetry_all", smoothing_window=15, poly_order=3, min_speed_drop=10, order=5, edge_buffer=30):
    con = duckdb.connect(DB_PATH)
    df = con.execute(f"""
        SELECT Distance, Speed, Throttle, Brake
        FROM {table}
        WHERE Driver = '{driver}'
        ORDER BY Distance
    """).df()
    con.close()

    df = df.dropna(subset=["Distance", "Speed"]).reset_index(drop=True)

    smoothed_speed = savgol_filter(df["Speed"], window_length=smoothing_window, polyorder=poly_order)
    df["SmoothedSpeed"] = smoothed_speed

    max_distance = df["Distance"].max()

    minima_idx = argrelextrema(smoothed_speed, np.less_equal, order=order)[0]
    minima_idx = np.unique(minima_idx)

    corners = []
    for idx in minima_idx:
        dist = df["Distance"].iloc[idx]
        if dist < edge_buffer or dist > (max_distance - edge_buffer):
            continue

        apex_speed = smoothed_speed[idx]
        window_start = max(0, idx - 20)
        window_end = min(len(smoothed_speed), idx + 20)
        local_max_speed = smoothed_speed[window_start:window_end].max()

        if local_max_speed - apex_speed >= min_speed_drop:
            corners.append({
                "apex_distance": dist,
                "apex_speed": apex_speed,
                "brake_at_apex": df["Brake"].iloc[idx],
                "throttle_at_apex": df["Throttle"].iloc[idx]
            })

    corners_df = pd.DataFrame(corners)
    if len(corners_df) > 0:
        corners_df = corners_df.sort_values("apex_distance").reset_index(drop=True)
        keep = [0]
        for i in range(1, len(corners_df)):
            if corners_df["apex_distance"].iloc[i] - corners_df["apex_distance"].iloc[keep[-1]] > 80:
                keep.append(i)
        corners_df = corners_df.iloc[keep].reset_index(drop=True)
        corners_df["corner_number"] = range(1, len(corners_df) + 1)
        corners_df["Driver"] = driver

    return corners_df, df

def detect_corners_all_drivers(drivers=None, table="telemetry_all"):
    con = duckdb.connect(DB_PATH)
    if drivers is None:
        drivers = con.execute(f"SELECT DISTINCT Driver FROM {table}").df()["Driver"].tolist()
    con.close()

    all_corners = []
    for driver in drivers:
        corners_df, _ = detect_corners(driver=driver, table=table)
        if len(corners_df) > 0:
            all_corners.append(corners_df)
        print(f"{driver}: {len(corners_df)} corners detected")

    combined = pd.concat(all_corners, ignore_index=True)
    return combined

if __name__ == "__main__":
    all_corners = detect_corners_all_drivers()
    print(f"\nTotal: {len(all_corners)} corner detections across {all_corners['Driver'].nunique()} drivers")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE corners_all AS SELECT * FROM all_corners")
    con.close()
    print("Saved corners_all table to DuckDB")