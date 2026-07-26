import duckdb
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter, argrelextrema

DB_PATH = "/app/data/processed/telemetry.duckdb"

def detect_corners(smoothing_window=15, poly_order=3, min_speed_drop=10, order=5, edge_buffer=30):
    con = duckdb.connect(DB_PATH)
    df = con.execute("SELECT Distance, Speed, Throttle, Brake FROM telemetry ORDER BY Distance").df()
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

    return corners_df, df

if __name__ == "__main__":
    corners_df, telemetry_df = detect_corners()
    print(f"Detected {len(corners_df)} corners")
    print(corners_df.to_string())

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE corners AS SELECT * FROM corners_df")
    con.close()
    print("Saved corners table to DuckDB")