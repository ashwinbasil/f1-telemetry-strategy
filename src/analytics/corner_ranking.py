import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def corner_ranking_all(zone_buffer=50):
    con = duckdb.connect(DB_PATH)
    corners = con.execute("SELECT * FROM corners_multi_race ORDER BY Race, Driver, corner_number").df()
    brake_points = con.execute("SELECT * FROM brake_points_multi_race ORDER BY Race, Driver, corner_number").df()
    delta = con.execute("SELECT * FROM delta_vs_fastest_multi_race ORDER BY Race, Driver, Distance").df()
    con.close()

    results = []
    for race in corners["Race"].unique():
        race_corners = corners[corners["Race"] == race]
        race_brake = brake_points[brake_points["Race"] == race]
        race_delta = delta[delta["Race"] == race]

        for driver in race_corners["Driver"].unique():
            driver_corners = race_corners[race_corners["Driver"] == driver]
            driver_brake = race_brake[race_brake["Driver"] == driver]
            driver_delta = race_delta[race_delta["Driver"] == driver]

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
                results.append({"Race": race, "Driver": driver, "corner_number": corner_num, "apex_distance": apex_dist, "delta_swing": delta_swing})

    ranking = pd.DataFrame(results)
    corner_avg = ranking.groupby(["Race", "corner_number"])["delta_swing"].mean().reset_index()
    corner_avg.columns = ["Race", "corner_number", "avg_time_lost"]
    corner_avg = corner_avg.sort_values(["Race", "avg_time_lost"], ascending=[True, False]).reset_index(drop=True)

    return ranking, corner_avg

if __name__ == "__main__":
    ranking, corner_avg = corner_ranking_all()
    print(f"Per-driver corner impact: {len(ranking)} rows across {ranking['Race'].nunique()} races")
    print(f"\nWorst corner per race (highest avg time lost):")
    worst_per_race = corner_avg.loc[corner_avg.groupby("Race")["avg_time_lost"].idxmax()]
    print(worst_per_race.to_string(index=False))

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE corner_ranking_multi_race AS SELECT * FROM ranking")
    con.execute("CREATE OR REPLACE TABLE corner_ranking_avg_multi_race AS SELECT * FROM corner_avg")
    con.close()
    print("\nSaved corner_ranking_multi_race and corner_ranking_avg_multi_race tables to DuckDB")