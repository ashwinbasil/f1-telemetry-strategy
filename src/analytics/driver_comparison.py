import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def driver_comparison_all():
    con = duckdb.connect(DB_PATH)
    df = con.execute("""
        SELECT Driver, LapNumber, LapTime_sec, Sector1Time_sec, Sector2Time_sec, Sector3Time_sec, Compound, Stint
        FROM sector_splits
        WHERE LapTime_sec IS NOT NULL
        ORDER BY Driver, LapNumber
    """).df()
    con.close()

    summary = df.groupby("Driver").agg(
        laps=("LapNumber", "count"),
        avg_lap=("LapTime_sec", "mean"),
        best_lap=("LapTime_sec", "min"),
        std_lap=("LapTime_sec", "std"),
        avg_s1=("Sector1Time_sec", "mean"),
        avg_s2=("Sector2Time_sec", "mean"),
        avg_s3=("Sector3Time_sec", "mean"),
    ).round(3).reset_index()

    summary = summary.sort_values("best_lap").reset_index(drop=True)
    summary["rank"] = range(1, len(summary) + 1)

    return summary, df

if __name__ == "__main__":
    summary, df = driver_comparison_all()
    print("Driver comparison summary, all 20 drivers, ranked by best lap:")
    print(summary.to_string(index=False))

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE driver_comparison_all AS SELECT * FROM summary")
    con.close()
    print("\nSaved driver_comparison_all table to DuckDB")