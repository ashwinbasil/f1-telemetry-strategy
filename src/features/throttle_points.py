import duckdb
import pandas as pd
from src.features.corner_detection import detect_corners

DB_PATH = "/app/data/processed/telemetry.duckdb"

def detect_throttle_points(lookahead_distance=200, throttle_threshold=20):
    corners_df, telemetry_df = detect_corners()

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
            "corner_number": corner["corner_number"],
            "apex_distance": apex_dist,
            "apex_speed": corner["apex_speed"],
            "throttle_at_apex": throttle_at_apex,
            "throttle_point_distance": throttle_point_dist,
            "throttle_point_speed": throttle_point_speed,
            "coasting_length": (throttle_point_dist - apex_dist) if throttle_point_dist is not None else None
        })

    throttle_df = pd.DataFrame(throttle_points)
    return throttle_df

if __name__ == "__main__":
    throttle_df = detect_throttle_points()
    print(f"Throttle points for {len(throttle_df)} corners")
    print(throttle_df.to_string())

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE throttle_points AS SELECT * FROM throttle_df")
    con.close()
    print("Saved throttle_points table to DuckDB")