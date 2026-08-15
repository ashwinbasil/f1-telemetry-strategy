import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def corner_ranking(zone_buffer=50):
    con = duckdb.connect(DB_PATH)
    corners = con.execute("SELECT * FROM corners ORDER BY corner_number").df()
    brake_points = con.execute("SELECT * FROM brake_points ORDER BY corner_number").df()
    delta = con.execute("SELECT * FROM delta_ver_lec ORDER BY Distance").df()
    con.close()

    results = []
    for _, corner in corners.iterrows():
        corner_num = corner["corner_number"]
        apex_dist = corner["apex_distance"]

        bp_row = brake_points[brake_points["corner_number"] == corner_num]
        zone_start = bp_row["brake_point_distance"].iloc[0] if len(bp_row) > 0 and pd.notna(bp_row["brake_point_distance"].iloc[0]) else apex_dist - zone_buffer
        zone_end = apex_dist + zone_buffer

        zone = delta[(delta["Distance"] >= zone_start) & (delta["Distance"] <= zone_end)]

        if len(zone) < 2:
            continue

        delta_swing = zone["Delta"].iloc[-1] - zone["Delta"].iloc[0]

        results.append({
            "corner_number": corner_num,
            "apex_distance": apex_dist,
            "zone_start": zone_start,
            "zone_end": zone_end,
            "delta_swing": delta_swing,
            "winner": "VER" if delta_swing < 0 else "LEC"
        })

    ranking = pd.DataFrame(results)
    ranking["abs_swing"] = ranking["delta_swing"].abs()
    ranking = ranking.sort_values("abs_swing", ascending=False).reset_index(drop=True)
    ranking["rank"] = range(1, len(ranking) + 1)

    return ranking

if __name__ == "__main__":
    ranking = corner_ranking()
    print("Corner ranking by time impact (VER vs LEC):")
    print(ranking[["rank", "corner_number", "delta_swing", "winner"]].to_string(index=False))

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE corner_ranking AS SELECT * FROM ranking")
    con.close()
    print("\nSaved corner_ranking table to DuckDB")