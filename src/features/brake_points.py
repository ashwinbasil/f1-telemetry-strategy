import duckdb

import pandas as pd

from src.features.corner_detection import detect_corners



DB_PATH = "/app/data/processed/telemetry.duckdb"



def detect_brake_points(lookback_distance=200):

    corners_df, telemetry_df = detect_corners()



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

            "corner_number": corner["corner_number"],

            "apex_distance": apex_dist,

            "apex_speed": corner["apex_speed"],

            "brake_point_distance": brake_point_dist,

            "brake_point_speed": brake_point_speed,

            "brake_zone_length": (apex_dist - brake_point_dist) if brake_point_dist is not None else None

        })



    brake_df = pd.DataFrame(brake_points)

    return brake_df



if __name__ == "__main__":

    brake_df = detect_brake_points()

    print(f"Brake points for {len(brake_df)} corners")

    print(brake_df.to_string())



    con = duckdb.connect(DB_PATH)

    con.execute("CREATE OR REPLACE TABLE brake_points AS SELECT * FROM brake_df")

    con.close()

    print("Saved brake_points table to DuckDB")
