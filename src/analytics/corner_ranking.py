import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def corner_ranking_all_drivers(zone_buffer=50):
    con = duckdb.connect(DB_PATH)
    corners = con.execute("SELECT * FROM corners_all ORDER BY Driver, corner_number").df()
    brake_points = con.execute("SELECT * FROM brake_points_all ORDER BY Driver, corner_number").df()
    delta = con.execute("SELECT * FROM delta_vs_fastest ORDER BY Driver, Distance").df()
    con.close()

    results = []
    for driver in corners["Driver"].unique():
        driver_corners = corners[corners["Driver"] == driver]
        driver_brake = brake_points[brake_points["Driver"] == driver]
        driver_delta = delta[delta["Driver"] == driver]

        if len(driver_delta) == 0:
            continue

        for _, corner in driver_corners.iterrows():
            corner_num = corner["corner_number"]
            apex_dist = corner["apex_distance"]

            bp_row = driver_brake[driver_brake["corner_number"] == corner_num]
            zone_start = bp_row["brake_point_distance"].iloc[0] if len(bp_row) > 0 and pd.notna(bp_row["brake_point_distance"].iloc[0]) else apex_dist - zone_buffer
            zone_end = apex_dist + zone_buffer

            zone = driver_delta[(driver_delta["Distance"] >= zone_start) & (driver_delta["Distance"] <= zone_end)]

            if len(zone) < 2:
                continue

            delta_swing = zone["Delta"].iloc[-1] - zone["Delta"].iloc[0]

            results.append({
                "Driver": driver,
                "corner_number": corner_num,
                "apex_distance": apex_dist,
                "delta_swing": delta_swing
            })

    ranking = pd.DataFrame(results)

    corner_avg = ranking.groupby("corner_number")["delta_swing"].mean().reset_index()
    corner_avg.columns = ["corner_number", "avg_time_lost"]
    corner_avg = corner_avg.sort_values("avg_time_lost", ascending=False).reset_index(drop=True)
    corner_avg["rank"] = range(1, len(corner_avg) + 1)

    return ranking, corner_avg

if __name__ == "__main__":
    ranking, corner_avg = corner_ranking_all_drivers()
    print("Per-driver corner impact (sample, first 10 rows):")
    print(ranking.head(10).to_string(index=False))

    print("\nCorners ranked by average time lost across field (vs fastest driver):")
    print(corner_avg.to_string(index=False))

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE corner_ranking_all AS SELECT * FROM ranking")
    con.execute("CREATE OR REPLACE TABLE corner_ranking_avg AS SELECT * FROM corner_avg")
    con.close()
    print("\nSaved corner_ranking_all and corner_ranking_avg tables to DuckDB")